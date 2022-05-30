## Mian Concepts

**Dataset**

`Dataset` include the data and metadate used during running the benchmark. They can be obtained by the `get_train` and `get_test` functions for training and testing tasks respectively. 

The benchmark framework will download the dataset from cloud for the first time and save the dataset to a cache directory. Later, user could access the data by setting the cache directory in the configuration file `benchmark.yaml`.


**Task**

`Task` means the training or testing task in `Benchmark`. They are used in `Player`. Tasks can be obtained by the `get_task` and `get_local_task` of the `tsbenchmark.api`.

`Task` consists of the following information:
- data，include training data and testing data
- metadata，include task type, data structure, horizon, time series field list, covariate field list,etc.
- training parameters，include random_state、reward_metric、max_trials, etc.


**Benchmark**

`Benchmark` makes the `players` performing defined `tasks` and integrates the results into one `report`.
The results of various players have differences in running time, evaluation scores,etc.

TSBenchmark currently supports two kinds of Benchmark implementation： 
- LocalBenchmark: running Benchmark locally
- RemoteSSHBenchmark: running benchmark remotely through SSH

**Player**

`Player` is used to run tasks。A player contains a Python script file and an operating environment description file. 
The Python script file could call functions from tsbenchmark api to obtain the detail task, training model, evaluation methods and dataset.

**Environment**

The operating environment of player can be either custom Python environment or virtual Python environment which are defined by the `requirement.txt` or `.yaml` file exported by conda respectively.


**Report**

`Report` is the output of the `Benchmark`, It collects the results from players and generates a comparison report, which contains the comparison results of both different players same benchmark and same player different benchmarks.

The results include the forecast results and the performance indicators, such as smape, mae, rmse, mape, etc.






