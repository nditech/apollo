# TODO: original used settings. change if necessary
BIG_N = 6000000


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

    f = m.sum(axis=0) / BIG_N
    k = m.size
    am = a * m

    return ((1 - f) / (k * mbarsquare)) * ((asquare.sum(axis=0) -
        2 * p * am.sum(axis=0) + psquare * msquare.sum(axis=0)) / (k - 1))
