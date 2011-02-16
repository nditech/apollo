# Create your views here.
from django.db.models import Q

queries = {}

queries['first'] = {}
queries['first']['complete']        = Q(submitted=True)
queries['first']['missing']         = Q(submitted=False)

queries['second'] = {}
queries['second']['complete']       = Q(A__in=[1,2,3]) & Q(B__gt=0) & Q(C__isnull=False) & Q(F__isnull=False) & Q(G__gt=0) & \
      (Q(D1__isnull=False) | Q(D2__isnull=False) | Q(D3__isnull=False) | Q(D4__isnull=False)) & \
      (Q(E1__isnull=False) | Q(E2__isnull=False) | Q(E3__isnull=False) | Q(E4__isnull=False) | \
      Q(E5__isnull=False))
queries['second']['missing']        = Q(A__isnull=True) & Q(B=0) & Q(C__isnull=True) & Q(F__isnull=True) & Q(G=0) & \
      (Q(D1__isnull=True) | Q(D2__isnull=True) | Q(D3__isnull=True) | Q(D4__isnull=True)) & \
      (Q(E1__isnull=True) | Q(E2__isnull=True) | Q(E3__isnull=True) | Q(E4__isnull=True) | \
      Q(E5__isnull=True))
queries['second']['partial']        = (Q(A__lt=4) | Q(B__gt=0) | Q(C__isnull=False) | Q(F__isnull=False) | Q(G__gt=0) | \
      Q(D1__isnull=False) | Q(D2__isnull=False) | Q(D3__isnull=False) | Q(D4__isnull=False) | \
      Q(E1__isnull=False) | Q(E2__isnull=False) | Q(E3__isnull=False) | Q(E4__isnull=False) | \
      Q(E5__isnull=False)) & ~(Q(A__in=[1,2,3,4]) & Q(B__gt=0) & Q(C__isnull=False) & Q(F__isnull=False) & Q(G__gt=0) & \
      (Q(D1__isnull=False) | Q(D2__isnull=False) | Q(D3__isnull=False) | Q(D4__isnull=False)) & \
      (Q(E1__isnull=False) | Q(E2__isnull=False) | Q(E3__isnull=False) | Q(E4__isnull=False) | \
      Q(E5__isnull=False)))
queries['second']['problem']        = (Q(B__gt=0) | Q(C__isnull=False) | Q(F__isnull=False) | Q(G__gt=0) | \
      Q(D1__isnull=False) | Q(D2__isnull=False) | Q(D3__isnull=False) | Q(D4__isnull=False) | \
      Q(E1__isnull=False) | Q(E2__isnull=False) | Q(E3__isnull=False) | Q(E4__isnull=False) | \
      Q(E5__isnull=False)) & Q(A=4) & Q(verified_second=False)
queries['second']['verified']       = (Q(A=4) & Q(verified_second=True)) | ((Q(B=0) & Q(C__isnull=True) & Q(F__isnull=True) & Q(G=0) & \
      (Q(D1__isnull=True) | Q(D2__isnull=True) | Q(D3__isnull=True) | Q(D4__isnull=True)) & \
      (Q(E1__isnull=True) | Q(E2__isnull=True) | Q(E3__isnull=True) | Q(E4__isnull=True) | \
      Q(E5__isnull=True))) & Q(A=4))

qs_complete = Q(H__isnull=False) & Q(J__isnull=False) & Q(K__isnull=False) & Q(M__isnull=False) & \
          Q(N__isnull=False) & Q(P__isnull=False) & Q(Q__isnull=False) & Q(R__isnull=False) & \
          Q(S__isnull=False) & Q(T__gt=0) & Q(U__gt=0) & Q(V__gt=0) & Q(W__gt=0) & Q(X__gt=0) & Q(Y__isnull=False) & \
          Q(Z__isnull=False) & Q(AA__isnull=False)
qs_missing = Q(H__isnull=True) & Q(J__isnull=True) & Q(K__isnull=True) & Q(M__isnull=True) & \
          Q(N__isnull=True) & Q(P__isnull=True) & Q(Q__isnull=True) & Q(R__isnull=True) & \
          Q(S__isnull=True) & Q(T=0) & Q(U=0) & Q(V=0) & Q(W=0) & Q(X=0) & Q(Y__isnull=True) & \
          Q(Z__isnull=True) & Q(AA__isnull=True)
qs_partial = (Q(H__isnull=False) | Q(J__isnull=False) | Q(K__isnull=False) | Q(M__isnull=False) | \
          Q(N__isnull=False) | Q(P__isnull=False) | Q(Q__isnull=False) | Q(R__isnull=False) | \
          Q(S__isnull=False) | Q(T__gt=0) | Q(U__gt=0) | Q(V__gt=0) | Q(W__gt=0) | Q(X__gt=0) | Q(Y__isnull=False) | \
          Q(Z__isnull=False) | Q(AA__isnull=False)) & ~(qs_complete)

queries['third'] = {}
queries['third']['complete']            = ~Q(A=4) & qs_complete
queries['third']['missing']             = ~Q(A=4) & qs_missing
queries['third']['partial']             = ~Q(A=4) & qs_partial
queries['third']['problem']             = ((Q(A=4) & qs_partial) | (Q(A=4) & qs_complete & Q(verified_third=False)))
queries['third']['verified']            = ((Q(A=4) & Q(verified_third=True) & qs_partial))
queries['third']['blank']               = Q(A=4) & qs_missing

queries['dco'] = {}
queries['dco']['arrival'] = {}
queries['dco']['arrival']['yes'] = Q(submitted=True)
queries['dco']['arrival']['no'] = Q(submitted=False)

queries['dco']['status'] = {}
queries['dco']['status']['missing'] = Q(A=0) & Q(B=0) & Q(C__isnull=True) & Q(D=0) & Q(E=0) & Q(F1__isnull=True) & \
    Q(F2__isnull=True) & Q(F3__isnull=True) & Q(F4__isnull=True) & Q(F5__isnull=True) & \
    Q(F6__isnull=True) & Q(F7__isnull=True) & Q(F8__isnull=True) & Q(F9__isnull=True) & \
    Q(G__isnull=True) & Q(H=0) & Q(J__isnull=True) & Q(K__isnull=True) & Q(M=0) & Q(N=0) & \
    Q(P=0) & Q(Q=0) & Q(R=0) & Q(S__isnull=True) & Q(T__isnull=True) & Q(U__isnull=True) & \
    Q(V__isnull=True) & Q(W__isnull=True) & Q(X__isnull=True)
queries['dco']['status']['not_open'] = Q(A=2) & Q(B=0) & Q(C__isnull=True) & Q(D=0) & Q(E=0) & Q(F1__isnull=True) & \
    Q(F2__isnull=True) & Q(F3__isnull=True) & Q(F4__isnull=True) & Q(F5__isnull=True) & \
    Q(F6__isnull=True) & Q(F7__isnull=True) & Q(F8__isnull=True) & Q(F9__isnull=True) & \
    Q(G__isnull=True) & Q(H=0) & Q(J__isnull=True) & Q(K__isnull=True) & Q(M=0) & Q(N=0) & \
    Q(P=0) & Q(Q=0) & Q(R=0) & Q(S__isnull=True) & Q(T__isnull=True) & Q(U__isnull=True) & \
    Q(V__isnull=True) & Q(W__isnull=True) & Q(X__isnull=True)

queries['dco']['status']['complete'] = Q(A=1) & Q(B__gt=0) & Q(C__isnull=False) & Q(D__gt=0) & Q(E__gt=0) & (Q(F1__isnull=False) | \
    Q(F2__isnull=False) | Q(F3__isnull=False) | Q(F4__isnull=False) | Q(F5__isnull=False) | \
    Q(F6__isnull=False) | Q(F7__isnull=False) | Q(F8__isnull=False) | Q(F9__isnull=False)) & \
    Q(G__isnull=False) & Q(H__gt=0) & Q(J__isnull=False) & Q(K__isnull=False) & Q(M__gt=0) & Q(N__gt=0) & \
    Q(P__gt=0) & Q(Q__gt=0) & Q(R__gt=0) & Q(S__isnull=False) & Q(T__isnull=False) & Q(U__isnull=False) & \
    Q(V__isnull=False) & Q(W__isnull=False) & Q(X__isnull=False) & Q(submitted=True)

queries['dco']['status']['partial'] = Q(A=1) & (Q(B__gt=0) | Q(C__isnull=False) & Q(D__gt=0) | Q(E__gt=0) | Q(F1__isnull=False) | \
    Q(F2__isnull=False) | Q(F3__isnull=False) | Q(F4__isnull=False) | Q(F5__isnull=False) | \
    Q(F6__isnull=False) | Q(F7__isnull=False) | Q(F8__isnull=False) | Q(F9__isnull=False) | \
    Q(G__isnull=False) | Q(H__gt=0) | Q(J__isnull=False) | Q(K__isnull=False) | Q(M__gt=0) | Q(N__gt=0) | \
    Q(P__gt=0) | Q(Q__gt=0) | Q(R__gt=0) | Q(S__isnull=False) | Q(T__isnull=False) | Q(U__isnull=False) | \
    Q(V__isnull=False) | Q(W__isnull=False) | Q(X__isnull=False) | Q(submitted=True)) & ~(queries['dco']['status']['complete'])

queries['dco']['status']['problem'] = Q(A=2) & (Q(B__gt=0) | Q(C__isnull=False) & Q(D__gt=0) | Q(E__gt=0) | Q(F1__isnull=False) | \
    Q(F2__isnull=False) | Q(F3__isnull=False) | Q(F4__isnull=False) | Q(F5__isnull=False) | \
    Q(F6__isnull=False) | Q(F7__isnull=False) | Q(F8__isnull=False) | Q(F9__isnull=False) | \
    Q(G__isnull=False) | Q(H__gt=0) | Q(J__isnull=False) | Q(K__isnull=False) | Q(M__gt=0) | Q(N__gt=0) | \
    Q(P__gt=0) | Q(Q__gt=0) | Q(R__gt=0) | Q(S__isnull=False) | Q(T__isnull=False) | Q(U__isnull=False) | \
    Q(V__isnull=False) | Q(W__isnull=False) | Q(X__isnull=False)) & ~(queries['dco']['status']['complete'])

