def incidents_csv(df, groupby, options):
    incidents = []
    if df.shape[0]:
        grouped = df.groupby(groupby)

        for group in grouped.groups.keys():
            entry = {}
            entry['LOC'] = group
            entry['TOT'] = int(df.ix[grouped.groups[group]].ix[:, options].fillna(0).sum().sum())
            for option in options:
                try:
                    entry[option] = int(df.ix[grouped.groups[group]][option].fillna(0).sum())
                except KeyError:
                    entry[option] = 0
            incidents.append(entry)
    return incidents
