from django.conf import settings


def proportion(df, options, param):
	m = df.ix[:, options].sum(axis=1, skipna=True)
	mbar = m.sum(axis=0, skipna=True) / m.size
	print 'mbar = {}\nk= {}'.format(mbar, m.size)
	return df.ix[:, param].sum(axis=0, skipna=True) / (mbar * m.size)


def variance(df, options, param):
	p = proportion(df, options, param)
	psquare = p * p

	m = df.ix[:, options].sum(axis=1, skipna=True)
	msquare = m * m

	a = df.ix[:, param]
	asquare = a * a

	mbar = m.sum(axis=0, skipna=True) / m.size
	mbarsquare = mbar * mbar

	f = m.sum(axis=0, skipna=True) / settings.BIG_N
	k = m.size
	am = a * m

	return ((1 - f) / (k * mbarsquare)) * ((asquare.sum(axis=0, skipna=True) - \
		2 * p * am.sum(axis=0, skipna=True) + psquare * msquare.sum(axis=0, skipna=True)) / (k - 1))
