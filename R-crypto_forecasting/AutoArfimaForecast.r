# install.packages("forecast")
# install.packages("tsbox")
# install.packages("lubridate")
# install.packages("knitr")
# install.packages("pracma")
# install.packages("arfima")
# install.packages("Metrics")
# install.packages("fracdiff")

args <- commandArgs(trailingOnly = TRUE)
# test if there is at least one argument: if not, return an error
if (length(args) == 0) {
    stop("At least one argument must be supplied (input file).n", call. = FALSE)
} else if (length(args) == 1) {
    args[2] <- "ClosePriceForecasted.csv"
    args[3] <- 7
    args[4] <- ""
} else if (length(args) == 2) {
    args[3] <- 7
    args[4] <- ""
} else if (length(args) == 3) {
    args[4] <- ""
}

main_dir <- paste("E://Projects/Master-Diploma/CryptoAnalyzer",
"/R-crypto_forecasting/", sep = "")
datasets_dir <- file.path(main_dir, "updated_datasets")
results_dir <- file.path(main_dir, "results")

dir.create(datasets_dir, showWarnings = FALSE)
dir.create(results_dir, showWarnings = FALSE)

# set working directory
setwd(datasets_dir)

# get crypto data
get_data <- function(file_name) {
    return(read.csv(file_name, header = T, na.string = "?"))
}

# create time series from crypto data
get_time_series <- function(ts_table) {
    start_full_date <- ts_table$Date[1]
    close_full_date <- ts_table$Date[length(ts_table$Date)]
    start_date <- strsplit(start_full_date, " ")[[1]][1]
    close_date <- strsplit(close_full_date, " ")[[1]][1]
    time_seq <- seq(from = as.Date(start_date),
                    to = as.Date(close_date),
                    by = 1)
    ts_data <- xts::xts(x = ts_table$Close, order.by = time_seq)
    return(tsbox::ts_ts(ts_data))
}

# export forecasted values to csv file
forecasted_to_csv <- function(dates, forecasted_vals, csv_path) {
    forecasted_df <- data.frame(Date = dates, Close = forecasted_vals)
    write.csv(forecasted_df,
              csv_path,
              row.names = FALSE,
              quote = FALSE)
}

# main function to train arfima model
arfima_modelling <- function(source_path, dest_path, horizon, timestamp) {
    btc_close <- get_data(source_path)

    forecast_date <- btc_close$Date[length(btc_close$Date)]
    forecast_date <- strsplit(forecast_date, " ")[[1]][1]

    ts_data <- get_time_series(btc_close)

    train <- ts_data

    model <- forecast::arfima(train)
    forecasted_out <- forecast::forecast(model, level = c(95), h = horizon)

    forecasted_dates_numeric <- as.numeric(
        row.names(as.data.frame(forecasted_out)))

    # generating range of dates
    forecasted_dates <- seq(as.Date(forecast_date),
                         by = "day",
                         length.out = horizon)

    forecasted_values <- forecasted_out[2]$mean

    png(file = file.path(results_dir,
     paste("ARFIMA_visual_forecast_", timestamp, ".png", sep = "")),
                         width = 900,
                         height = 700)
    par(c(1, 1))
    plot(forecasted_out,
         xaxt = "n",
         xlab = "Date",
         ylab = "Bitcoin close price (USD)",
         xlim = c(time(train)[length(train) - 60],
                forecasted_dates_numeric[length(forecasted_dates_numeric)]),
        #  main = "ARFIMA model predictions",
         showgap = FALSE,
         shadecols = "#205bff6a",
         fcol = "#1d1dff")
    axis(1,
         time(ts_data),
         format(lubridate::date_decimal(as.numeric(time(ts_data))), "%Y-%m-%d"))
    dev.off()

    forecasted_to_csv(forecasted_dates,
                      forecasted_values,
                      file.path(results_dir, dest_path))

    sink(file = file.path(results_dir,
     paste("ARFIMA_output_", timestamp, ".txt", sep = "")))
    print(forecast::arimaorder(model))
    sink(file = NULL)
}

arfima_modelling(args[1], args[2], as.numeric(args[3]), args[4])
# arfima_modelling("BTCClosePrice.csv", "BTCClosePriceForecasted.csv", 30)
