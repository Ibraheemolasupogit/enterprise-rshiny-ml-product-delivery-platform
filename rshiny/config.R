config_source <- if (dir.exists("R")) {
  file.path("R", "app_config.R")
} else {
  file.path("rshiny", "R", "app_config.R")
}
source(config_source, local = TRUE)

app_config <- load_app_config()
