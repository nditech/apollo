from django.conf import settings


def proportion(df, options, param):
    m = df.ix[:, options].sum(axis=1)
    mbar = m.sum(axis=0) / m.size
    return df.ix[:, param].sum(axis=0).sum(axis=0) / (mbar * m.size)


def variance(df, options, param):
    p = proportion(df, options, param)
    psquare = p * p

    m = df.ix[:, options].sum(axis=1)
    msquare = m * m

    a = df.ix[:, param].sum(axis=1)
    asquare = a * a

    mbar = m.sum(axis=0) / m.size
    mbarsquare = mbar * mbar

    f = m.sum(axis=0) / settings.BIG_N
    k = m.size
    am = a * m

    return ((1 - f) / (k * mbarsquare)) * ((asquare.sum(axis=0) - \
        2 * p * am.sum(axis=0) + psquare * msquare.sum(axis=0)) / (k - 1))


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
