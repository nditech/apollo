import pandas as pd


def aggregated_dataframe(queryset, form):
    agg_locations = [anc.location_type for anc in
                     queryset.first().location.ancestors]
    # change order of locations so the largest is first
    agg_locations.reverse()
    df_submissions = queryset.to_dataframe()
    all_fields = []

    # iterate through fields
    for group in form.groups:
        for field in group.fields:
            # multiselect options field
            if field.options:
                # column options are in the format tagname|option
                # e.g. (AB|1, AB|2, ...)
                # initialize the default value counts for each option
                default_options = {'{}|{}'.format(field.name, option): 0
                                   for option in field.options.values()}
                all_fields.extend(sorted(default_options.keys()))
                col = df_submissions.pop(field.name).tolist()
                for i, r in enumerate(col):
                    options = default_options.copy()
                    # multivalued fields have a list of values
                    if type(r) == list:
                        for o in r:
                            if o in field.options.values():
                                options['{}|{}'.format(field.name, o)] = 1
                    else:
                        if r in field.options.values():
                            options['{}|{}'.format(field.name, r)] = 1
                    col[i] = options
                df = pd.DataFrame(col)
                df_submissions = df_submissions.join(df)
            else:
                all_fields.append(field.name)

    # group and aggregate
    df_agg = pd.DataFrame(columns=agg_locations + all_fields)
    for idx in range(len(agg_locations)):
        grouping = agg_locations[:idx+1]
        for group_name, group_df in df_submissions.groupby(grouping):
            data_series = group_df.sum()[all_fields]
            if len(grouping) == 1:
                data_series[grouping[0]] = group_name
            elif len(grouping) > 1:
                for i, g in enumerate(grouping):
                    data_series[g] = group_name[i]
            df_agg = df_agg.append(data_series, ignore_index=True)

    df_agg = df_agg.fillna("")

    return df_agg
