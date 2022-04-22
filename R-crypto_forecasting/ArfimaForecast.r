# install.packages("forecast")
# install.packages("tsbox")
# install.packages("lubridate")
# install.packages("knitr")
# install.packages("pracma")
# install.packages("arfima")
# install.packages("Metrics")
# install.packages("fracdiff")

# set working directory
setwd(paste("E://Projects/Master-Diploma/CryptoAnalyzer",
"/R-crypto_forecasting/updated_datasets", sep = ""))

# get crypto data
get_data <- function(file_name) {
    return(read.csv(file_name, header = T, na.string = "?"))
}

# create time series from crypto data
get_time_series <- function(ts_table) {
    library(xts)
    library(tsbox)
    start_full_date <- ts_table$Date[1]
    close_full_date <- ts_table$Date[length(ts_table$Date)]
    start_date <- strsplit(start_full_date, " ")[[1]][1]
    close_date <- strsplit(close_full_date, " ")[[1]][1]
    time_seq <- seq(from = as.Date(start_date),
                    to = as.Date(close_date),
                    by = 1)
    train <- xts::xts(x = ts_table$Close, order.by = time_seq)
    return(tsbox::ts_ts(train))
}

# export forecasted values to csv file
forecasted_to_csv <- function(dates, forecasted_vals, csv_path) {
    forecasted_df <- data.frame(Date = dates, Close = forecasted_vals)
    write.csv(forecasted_df,
              csv_path,
              row.names = FALSE,
              quote = FALSE)
}

# find best arfima model from input quantity of ar and ma parameters
find_best_arfima_model <- function(ar_params, ma_params, train) {
    min_mse <- Inf
    return_params <- c(0, 0, 0)

    for (ar in ar_params) {
        for(ma in ma_params) {
            d_test <- fracdiff::fracdiff(train, nar = ar, nma = ma)$d
            model_arfima_test <- arfima::arfima(train,
                                    order = c(ar, ma, d_test),
                                    numeach = c(1, 1))
            forecasted_arfima_test <- predict(model_arfima_test,
                                    n.ahead = 30)
            forecasted_arfima_test_vals <- forecasted_arfima_test[[1]]$Forecast
            test_mse <- Metrics::rmse(test, forecasted_arfima_test_vals)

            if (min_mse > test_mse) {
                min_mse <- test_mse
                return_params <- c(ar, ma, d_test)
            }
        }
    }

    return(return_params)
}

btc_close <- get_data("BitcoinTransformedClose.csv")
# fix(btc_close)

ts_data <- get_time_series(btc_close)

# get Hurst exponent using R/S analysis
print(pracma::hurstexp(ts_data))

train <- head(ts_data, -30)
# train <- tail(head(ts_data, -30), 500)
test <- tail(ts_data, 30)

# forecast::tsdisplay(train, main = "Bitcoin close price")

cat("\n")

horizon <- 30

# time measuring of auto arfima modeling and forecasting
start_time <- Sys.time()

model <- forecast::arfima(train)
print(summary(model))
# forecast::tsdisplay(model$residuals, main = "Residuals")
forecasted_out <- forecast::forecast(model, level = c(95), h = horizon)

end_time <- Sys.time()
time_taken <- end_time - start_time

cat("\n")
print(time_taken)

forecasted_dates_numeric <- as.numeric(row.names(as.data.frame(forecasted_out)))

forecasted_values <- forecasted_out[2]$mean
forecasted_dates <- format(lubridate::date_decimal(forecasted_dates_numeric),
                    "%Y-%m-%d")

# par(c(1, 1))
# plot(forecasted_out,
#      xaxt = "n",
#      xlab = "Date",
#      ylab = "Bitcoin close price (USD)",
#      xlim = c(time(train)[length(train) - 60],
#             forecasted_dates_numeric[length(forecasted_dates_numeric)]),
#     #  main = "ARFIMA model predictions",
#      showgap = FALSE,
#      shadecols = "#205bff6a",
#      fcol = "#1d1dff")
# axis(1,
#      time(ts_data),
#      format(lubridate::date_decimal(as.numeric(time(ts_data))), "%Y-%m-%d"))


# forecasted_to_csv(forecasted_dates,
#                   forecasted_values,
#                   "BitcoinForecasted.csv")
cat("\n")
print(forecast::arimaorder(model))
print("ARFIMA accuracy: ")
print(forecast::accuracy(forecasted_out, test))

# auto arima modelling and forecasting
model_arima <- forecast::auto.arima(train)
forecasted_arima_out <- forecast::forecast(model_arima,
                                  level = c(95),
                                  h = horizon)
cat("\n")
print(forecast::arimaorder(model_arima))
print("ARIMA accuracy: ")
print(forecast::accuracy(forecasted_arima_out, test))
cat("\n")

# manually fitted arfima modeling and forecasting
m_gph <- fracdiff::fdGPH(train)
diff_train <- fracdiff::diffseries(train, d = m_gph$d)
forecast::tsdisplay(diff_train, main = "Differenciated BTC close price")

# from acf and pacf plots get significant spikes
ar_params <- c(0, 1, 2, 3, 4, 5, 6)
ma_params <- c(0, 1, 2, 3, 4, 5, 6, 7, 8, 9)

oldw <- getOption("warn")
options(warn = -1)
param_vec <- (find_best_arfima_model(ar_params, ma_params, train))
options(warn = oldw)

ar_param <- param_vec[1]
ma_param <- param_vec[2]
d_param <- param_vec[3]

model_arfima_man <- arfima::arfima(train,
                                   order = c(ar_param, ma_param, d_param),
                                   numeach = c(1, 1))
forecasted_arfima_man_out <- predict(model_arfima_man,
                                     n.ahead = 30)

# plot(residuals(model_arfima_man)[[1]],
#                ylab = "",
#                type = "b",
#                main = "Residuals")

forecasted_arfima_man_values <- forecasted_arfima_man_out[[1]]$Forecast

cat("\n")
print("p d q")
print(paste(ar_param, d_param, ma_param))
print("ARFIMA manually fitted accuracy: ")
cat("\n")
print(paste0("Test set RMSE: ",
             Metrics::rmse(test, forecasted_arfima_man_values)))
print(paste0("Test set MAPE (%): ",
             Metrics::mape(test, forecasted_arfima_man_values) * 100))

# models comparison using AIC statistics
print(knitr::kable(AIC(model, model_arima, model_arfima_man)))
cat("\n")
