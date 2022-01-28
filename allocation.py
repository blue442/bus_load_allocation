import pandas as pd


def gen_weighted_normalized_array(bus_df, random_uniform=True):
    """
    Creates an array of random numbers drawn from a
    distribution and normalized so they sum to 1.
    """    
    if random_uniform:
        bus_df['p'] = np.random.rand(bus_df.shape[0]) * bus_df['weight']
    else:
        bus_df['p'] = np.random.normal(100, 1, bus_df.shape[0]) * bus_df['weight']
    normalized_array = list(bus_df['p']/bus_df['p'].sum())
    return normalized_array


def gen_weighted_bus_class_allocations(load_dist_df, bus_df):
    """
    For each bus in the bus_df, this function will generate a
    value that corresponds to the proporition of total load by each
    load class that is distributed to that bus.
    """
    results = {}
    
    for load_class in load_dist_df['load_class'].unique():
        results[load_class] = gen_weighted_normalized_array(bus_df, random_uniform=True)
    
    result = pd.DataFrame(results).set_index(np.array(list(bus_df['bus_id']))).transpose()

    df = result.reset_index().melt('index').rename(columns={'index':'load_class', 'variable':'bus_number', 'value': 'class_bus_allocation'})
    
    return df


def calculate_weighted_bus_loads(zonal_load, season, day, hour, bus_signatures, utility_distribution_df):
    
    """
    Function to calculate loads for each bus by load_class for a given season, day, hour, 
    total zonal load, and load class distribution from a utility
    """

    # create a copy to store the output
    output_df = bus_signatures.copy(deep=True)
    
    # decompose the total zonal load to load_classes based on SDH
    zone_load_decompositon = utility_distribution_df.query(f"Season=='{season}' & DayType=='{day}' & hour=={hour}").merge(bus_signatures, on='load_class')
    
    # calculate the class x SDH load for each zone
    zone_load_decompositon[f"{season}_{day}_{hour}"] = zonal_load * zone_load_decompositon['p_total_load'] * zone_load_decompositon['class_bus_allocation']
    
    # append the result to a new column in the output dataframe
    output_df = output_df.merge(zone_load_decompositon[[f"{season}_{day}_{hour}", 'bus_number', 'load_class']], on=['bus_number', 'load_class'])

    return output_df


def iterate_weighted_bus_load_calculations_over_zones(sdhz_df, utility_distribution_df, bus_df):
    
    """
    Function to apply calculation of loads by bus and class given a range of Season,
    Day, Hour, and total zonal load distributions.
    """
    
    results_dfs = []
    
    for zone in bus_df['zone'].unique():
        
        # bus_list = list(bus_df.iloc[:,0])
        bus_zone_df = bus_df[bus_df['zone']==zone]
        load_df = sdhz_df[sdhz_df['zone']==zone]
        
        # calculate bus signatures
        bus_signatures = gen_weighted_bus_class_allocations(utility_distribution_df, bus_zone_df)

        results = []
        for idx, row in load_df.iterrows():

            # calculate bus loads for a single SDHZ
            result_df = calculate_weighted_bus_loads(row.zonal_load, 
                                                     row.Season, 
                                                     row.Day, 
                                                     row.hour, 
                                                     bus_signatures,
                                                     utility_distribution_df)

            # re-jigger
            result_df = result_df.drop('class_bus_allocation', axis=1)
            result_df = result_df.melt(id_vars=['load_class', 'bus_number'])
            result_df = result_df.rename(columns={'variable':'SDH', 'value':'load'})
            results.append(result_df)

        results_df = pd.concat(results)
        results_df[['Season', 'Day', 'Hour']] = results_df.SDH.str.split("_", expand=True)
        results_df = results_df.drop('SDH', axis=1)
        results_df['zone'] = zone
        results_dfs.append(results_df)
    
    return pd.concat(results_dfs)


def allocate_load(sdhz_csv, bus_csv, output_filename):
    
    input_df = pd.read_csv(sdhz_csv)
    bus_df = pd.read_csv(bus_csv)
    result = iterate_weighted_bus_load_calculations_over_zones(input_df, SDH_profiles_df, bus_df)
    result.to_csv(output_filename, index=False)