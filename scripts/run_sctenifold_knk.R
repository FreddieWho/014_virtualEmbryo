#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 5) {
  stop("usage: run_sctenifold_knk.R <counts.mtx> <genes.tsv> <target> <output.tsv> <seed>")
}
counts_path <- args[[1]]
genes_path <- args[[2]]
target <- args[[3]]
output_path <- args[[4]]
seed <- as.integer(args[[5]])

suppressPackageStartupMessages({
  library(Matrix)
  library(scTenifoldNet)
  library(scTenifoldKnk)
})
set.seed(seed)
count_matrix <- readMM(counts_path)
gene_table <- read.delim(genes_path, header = TRUE, stringsAsFactors = FALSE, check.names = FALSE)
rownames(count_matrix) <- gene_table$gene
colnames(count_matrix) <- paste0("cell_", seq_len(ncol(count_matrix)))
if (!target %in% rownames(count_matrix)) stop(paste("target absent from matrix:", target))

result <- scTenifoldKnk(
  count_matrix,
  gKO = target,
  qc = TRUE,
  qc_minLibSize = 0,
  qc_removeOutlierCells = FALSE,
  qc_minPCT = 0,
  qc_maxMTratio = 1,
  nc_nComp = 3,
  nc_q = 0.85,
  nc_lambda = 0.7,
  nc_nCells = 500,
  nCores = 1
)
diff <- result$diffRegulation
if (is.null(diff)) stop("scTenifoldKnk did not return diffRegulation")
version_output <- paste0(output_path, ".versions.tsv")
version_table <- data.frame(
  package = c("R", "Matrix", "scTenifoldNet", "scTenifoldKnk"),
  version = c(
    paste(R.version$major, R.version$minor, sep = "."),
    as.character(packageVersion("Matrix")),
    as.character(packageVersion("scTenifoldNet")),
    as.character(packageVersion("scTenifoldKnk"))
  ),
  stringsAsFactors = FALSE
)
write.table(version_table, file = version_output, sep = "\t", quote = FALSE, row.names = FALSE)
write.table(diff, file = output_path, sep = "\t", quote = FALSE, row.names = FALSE)
