
for i in {1..30};
do
    python3.7 example3.py | tee log/example3_${i};
done
