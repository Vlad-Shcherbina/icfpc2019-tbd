_c="icfpcontest2019.github.io"

[ -d $_c ] && \
  echo "Found scraped directory. If you want to update, run “rm -rf $_c” first." && exit -666 || \
  wget -mk https://icfpcontest2019.github.io/solution_checker/

cd "$_c/download/"
for x in *zip; do
  unzip $x
done
