#!/usr/bin/env Rscript

source("renv/activate.R")

staged_packages <- c("zip", "chromote", "shinytest2")

for (package in staged_packages) {
  renv::restore(packages = package, prompt = FALSE)
}

renv::restore(prompt = FALSE)
