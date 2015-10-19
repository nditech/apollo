from flask import current_app


def proportion(df, options, param):
    m = df.ix[:, options].sum(axis=1)
    mbar = m.sum(axis=0) / m.size
    return df.ix[:, param].sum(axis=0).sum(axis=0) / (mbar * m.size)


def variance(df, options, param):
    p = proportion(df, options, param)
    psquared = p * p

    m = df.ix[:, options].sum(axis=1)
    msquared = m * m

    a = df.ix[:, param].sum(axis=1)
    asquared = a * a

    mbar = m.sum(axis=0) / m.size
    mbarsquared = mbar * mbar

    f = m.sum(axis=0) / current_app.config.get('BIG_N')
    k = m.size
    am = a * m
    sigma_asquared = asquared.sum(axis=0)
    sigma_msquared = msquared.sum(axis=0)
    sigma_am = am.sum(axis=0)

    return (
        (1 - f) / (k * mbarsquared)) * ((sigma_asquared -
                                        2 * p * sigma_am +
                                        psquared *
                                        sigma_msquared) / (k - 1))
