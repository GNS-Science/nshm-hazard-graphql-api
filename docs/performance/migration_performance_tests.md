# Comparing preformance between legacy THS and new dataset THS opptions

Here we use the script `scripts/perf_test` to perform some performance tests on the different data storage options.

These test matter because they impact the NSHM Kororaa Hazard charts performance. Too slow, and our users will be disappointed, also lambda 
costs are per millisecond so it'll cost more. Basically, faster is better for users AND it's cheaper.

We use a graphql query that is typical for the **NSHM Kororaa** `/Hazardcurves` view.
By default, this view retrieves 80 curves from the backend, 16 IMT levels and 5 aggregations per vs30/location.

In these tests, the type indicates query strategy used, where:
 - `dyn` is the legacy THS dynamoDB query (which we're migrating awawy from for cost reasons)
 - `d2` is a set of pyarrow queries split by vs30/location partitioning.
 - `d1` is a set of pyarrow queries split by vs30 partition.
 - `d0` is a single pyarrow query. (tests Omitted as theyre, not tractable)
 
The other columns:
 - `curves` is the count of hazard curves returned bythe query. 
 - `result` indicates if the query suceeded, or not. 
    Usually a failure would be due to API Gateway timeout (20 sec) but shorter failures are likely out-of-memory abends.


### July 3, 2025 lambda memory 4096 MB

```
>>> poetry run python nshm_hazard_graphql_api/scripts/perf_test.py
curves	vs30	location	type	duration (s)	result
80	400	WLG	dyn	0.827743	OK
0	400	WLG	d2	0.241829	OK
0	400	WLG	d1	1.948918	OK
80	1500	WLG	dyn	0.839087	OK
0	1500	WLG	d2	0.150123	OK
0	1500	WLG	d1	1.957228	OK
80	400	-41.300~174.800	dyn	10.50912	OK
80	400	-41.300~174.800	d2	9.900757	OK
80	400	-41.300~174.800	d1	11.567894	OK
80	1500	-41.300~174.800	dyn	10.427414	OK
80	1500	-41.300~174.800	d2	10.123958	OK
80	1500	-41.300~174.800	d1	11.597981	OK
80	400	-37.100~175.100	dyn	10.516899	OK
80	400	-37.100~175.100	d2	9.885756	OK
80	400	-37.100~175.100	d1	11.505476	OK
80	1500	-37.100~175.100	dyn	10.525181	OK
80	1500	-37.100~175.100	d2	10.372284	OK
80	1500	-37.100~175.100	d1	11.607133	OK
```

### July 3, 2025 lambda memory 1024 MB

```
curves	vs30	location	type	duration (s)	result
80	400	WLG	dyn	1.029025	OK
0	400	WLG	d2	0.56479	OK
0	400	WLG	d1	20.212452	FAIL
80	1500	WLG	dyn	2.299354	OK
0	1500	WLG	d2	0.596939	OK
0	1500	WLG	d1	18.079869	FAIL
80	400	-41.300~174.800	dyn	20.240017	OK
80	400	-41.300~174.800	d2	18.280459	OK
0	400	-41.300~174.800	d1	20.319864	FAIL
80	1500	-41.300~174.800	dyn	20.324972	OK
80	1500	-41.300~174.800	d2	18.198275	OK
0	1500	-41.300~174.800	d1	14.29723	FAIL
80	400	-37.100~175.100	dyn	20.105806	OK
80	400	-37.100~175.100	d2	18.298021	OK
0	400	-37.100~175.100	d1	14.811197	FAIL
80	1500	-37.100~175.100	dyn	20.040821	OK
80	1500	-37.100~175.100	d2	18.447579	OK
0	1500	-37.100~175.100	d1	13.368375	FAIL
```

### July 3, 2025 lambda memory 8192 MB

```
curves	vs30	location	type	duration (s)	result
80	400	WLG	dyn	0.844912	OK
0	400	WLG	d2	0.15127	OK
0	400	WLG	d1	1.994693	OK
80	1500	WLG	dyn	0.932414	OK
0	1500	WLG	d2	0.444737	OK
0	1500	WLG	d1	4.537489	OK
80	400	-41.300~174.800	dyn	10.659002	OK
80	400	-41.300~174.800	d2	10.071022	OK
80	400	-41.300~174.800	d1	11.62207	OK
80	1500	-41.300~174.800	dyn	10.488716	OK
80	1500	-41.300~174.800	d2	10.056161	OK
80	1500	-41.300~174.800	d1	11.658681	OK
80	400	-37.100~175.100	dyn	10.607774	OK
80	400	-37.100~175.100	d2	10.214583	OK
80	400	-37.100~175.100	d1	11.600485	OK
80	1500	-37.100~175.100	dyn	10.6275	OK
80	1500	-37.100~175.100	d2	10.217225	OK
80	1500	-37.100~175.100	d1	11.465013	OK
```

### July 4, 2025 lambda memory 8192 MB

using `toshi-hazard-store 1.1.2` 
removed WLG

```
poetry run python nshm_hazard_graphql_api/scripts/perf_test.py
curves	vs30	location	type	duration (s)	result
80	400	-41.300~174.800	dyn	8.518689	OK
80	400	-41.300~174.800	d2	7.873848	OK
80	400	-41.300~174.800	d1	9.105736	OK
0	400	-41.300~174.800	d0	20.342372	FAIL
80	1500	-41.300~174.800	dyn	9.573881	OK
80	1500	-41.300~174.800	d2	8.333735	OK
80	1500	-41.300~174.800	d1	10.614086	OK
0	1500	-41.300~174.800	d0	20.30217	FAIL
80	400	-37.100~175.100	dyn	9.394449	OK
80	400	-37.100~175.100	d2	8.103374	OK
80	400	-37.100~175.100	d1	11.181969	OK
0	400	-37.100~175.100	d0	20.359491	FAIL
80	1500	-37.100~175.100	dyn	9.427129	OK
80	1500	-37.100~175.100	d2	8.154325	OK
80	1500	-37.100~175.100	d1	10.642745	OK
0	1500	-37.100~175.100	d0	20.355737	FAIL
```

```
poetry run python nshm_hazard_graphql_api/scripts/perf_test.py
curves	vs30	location	type	duration (s)	result
80	400	-41.300~174.800	dyn	10.37418	OK
80	400	-41.300~174.800	d2	9.709453	OK
80	400	-41.300~174.800	d1	14.637477	OK
0	400	-41.300~174.800	d0	20.375901	FAIL
80	1500	-41.300~174.800	dyn	11.579813	OK
80	1500	-41.300~174.800	d2	10.123966	OK
80	1500	-41.300~174.800	d1	13.11976	OK
0	1500	-41.300~174.800	d0	20.377911	FAIL
80	400	-37.100~175.100	dyn	12.202676	OK
80	400	-37.100~175.100	d2	10.227387	OK
80	400	-37.100~175.100	d1	13.091402	OK
0	400	-37.100~175.100	d0	20.389956	FAIL
80	1500	-37.100~175.100	dyn	11.633846	OK
80	1500	-37.100~175.100	d2	10.041962	OK
80	1500	-37.100~175.100	d1	13.030009	OK
0	1500	-37.100~175.100	d0	20.415737	FAIL
```

### July 4, 2025 lambda memory 10240 MB

```
poetry run python nshm_hazard_graphql_api/scripts/perf_test.py
curves	vs30	location	type	duration (s)	result
80	400	-41.300~174.800	dyn	13.115274	OK
80	400	-41.300~174.800	d2	10.397033	OK
80	400	-41.300~174.800	d1	13.880397	OK
0	400	-41.300~174.800	d0	20.395838	FAIL
80	1500	-41.300~174.800	dyn	11.789192	OK
80	1500	-41.300~174.800	d2	10.052416	OK
80	1500	-41.300~174.800	d1	13.079192	OK
0	1500	-41.300~174.800	d0	20.411192	FAIL
80	400	-37.100~175.100	dyn	11.662037	OK
80	400	-37.100~175.100	d2	10.307829	OK
80	400	-37.100~175.100	d1	13.183252	OK
0	400	-37.100~175.100	d0	20.475739	FAIL
80	1500	-37.100~175.100	dyn	11.796206	OK
80	1500	-37.100~175.100	d2	10.294681	OK
80	1500	-37.100~175.100	d1	13.207218	OK
0	1500	-37.100~175.100	d0	20.404699	FAIL
chrisbc@MLX01 nshm-hazard-graphql-api %
```

### July 4, 2025 Local (more net latency, more CPU)

```
curves	vs30	location	type	duration (s)	result
80	400	-41.300~174.800	dyn	7.226757	OK
80	400	-41.300~174.800	d2	5.024692	OK
80	400	-41.300~174.800	d1	3.890905	OK
80	400	-41.300~174.800	d0	3.884685	OK
80	1500	-41.300~174.800	dyn	7.371884	OK
80	1500	-41.300~174.800	d2	3.900103	OK
80	1500	-41.300~174.800	d1	3.862612	OK
80	1500	-41.300~174.800	d0	3.730971	OK
80	400	-37.100~175.100	dyn	6.991284	OK
80	400	-37.100~175.100	d2	3.904357	OK
80	400	-37.100~175.100	d1	3.746712	OK
80	400	-37.100~175.100	d0	3.737549	OK
80	1500	-37.100~175.100	dyn	6.979547	OK
80	1500	-37.100~175.100	d2	4.010305	OK
80	1500	-37.100~175.100	d1	3.755238	OK
80	1500	-37.100~175.100	d0	3.732168	OK
```

 - for nloc_001 location the new d0 strategy (pure pyarrow) is faster we don't have WLG in pyarrow, so can't test this.
 - fOR WLG (the Named Location is significantly faster) - why?? THS query is doing extra work?? is this applicable.

### Local 

chrisbc@MLX01 nshm-hazard-graphql-api % API_TOKEN=c0pWTQWUkl4bO1CvwYvWt85qiLfU6jwJ9DmQiKzW  poetry run python nshm_hazard_graphql_api/scripts/perf_test.py
curves	vs30	location	type	duration (s)	result
80	400	-41.300~174.800	dyn	7.046493	OK
80	400	WLG	dyn	4.09537	OK

#### With lru_cache on match_named_location_coord_code() 

```
poetry run python nshm_hazard_graphql_api/scripts/perf_test.py
curves	vs30	location	type	duration (s)	result
80	400	-41.300~174.800	dyn	4.312123	OK
80	400	-41.300~174.800	d2	2.172088	OK
80	400	-41.300~174.800	d1	1.034076	OK
80	400	-41.300~174.800	d0	1.032408	OK
chrisbc@MLX01 nshm-hazard-graphql-api %
```

```
curves	vs30	location	type	duration (s)	result
80	400	-41.300~174.800	dyn	4.258035	OK
80	400	-41.300~174.800	d0	2.211613	OK
80	1500	-41.300~174.800	dyn	4.015552	OK
80	1500	-41.300~174.800	d0	0.701373	OK
80	400	-37.100~175.100	dyn	3.863803	OK
80	400	-37.100~175.100	d0	0.770962	OK
80	1500	-37.100~175.100	dyn	4.019573	OK
80	1500	-37.100~175.100	d0	0.860143	OK
```

```
curves	vs30	location	type	duration (s)	result
80	400	-41.300~174.800	dyn	3.826717	OK
80	400	-41.300~174.800	d0	0.319117	OK
80	1500	-41.300~174.800	dyn	3.83676	OK
80	1500	-41.300~174.800	d0	0.181398	OK
80	400	-37.100~175.100	dyn	3.968629	OK
80	400	-37.100~175.100	d0	0.18462	OK
80	1500	-37.100~175.100	dyn	3.829918	OK
80	1500	-37.100~175.100	d0	0.18714	OK
```

### July 4, 2025 lambda memory 3096 MB

With latest code improvements we can get best performance using `d2` strategy, beating dynamoDB by x2. 

```
curves	vs30	location	type	duration (s)	result
80	400	WLG	dyn	0.756373	OK
0	400	WLG	d1	2.005263	OK
0	400	WLG	d2	0.14252	OK
80	1500	WLG	dyn	0.710936	OK
0	1500	WLG	d1	1.919604	OK
0	1500	WLG	d2	0.148006	OK
80	400	-41.300~174.800	dyn	0.754214	OK
80	400	-41.300~174.800	d1	2.050188	OK
80	400	-41.300~174.800	d2	0.413698	OK
80	1500	-41.300~174.800	dyn	0.737089	OK
80	1500	-41.300~174.800	d1	2.114472	OK
80	1500	-41.300~174.800	d2	0.343881	OK
80	400	-37.100~175.100	dyn	0.900393	OK
80	400	-37.100~175.100	d1	1.97574	OK
80	400	-37.100~175.100	d2	0.438934	OK
80	1500	-37.100~175.100	dyn	0.714019	OK
80	1500	-37.100~175.100	d1	2.045968	OK
80	1500	-37.100~175.100	d2	0.389187	OK
chrisbc@MLX01 nshm-hazard-graphql-api %
```