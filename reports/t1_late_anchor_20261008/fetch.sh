set -e
for s in GSM7226268_E8_5_1 GSM7226269_E8_5_2 GSM7226272_E14_5_1 GSM7226273_E14_5_2 GSM7226274_E16_5_1 GSM7226276_E16_5_2; do
  g=${s%%_*}
  for f in barcodes.tsv.gz features.tsv.gz matrix.mtx.gz; do
    [ -s ${s}_$f ] || curl -sS --retry 3 -o ${s}_$f https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM7226nnn/$g/suppl/${s}_$f
  done
  echo done $s
done
ls -la; du -sh .
