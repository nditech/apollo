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

queries['dco']['status']['complete'] = Q(A=1) & Q(B__gt=0) & Q(C__isnull=False) & Q(D__gt=0) & Q(E__gt=0) & (~Q(F1=False) | \
    ~Q(F2=False) | ~Q(F3=False) | ~Q(F4=False) | ~Q(F5=False) | \
    ~Q(F6=False) | ~Q(F7=False) | ~Q(F8=False) | ~Q(F9=False)) & \
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


queries['eday'] = {}
queries['eday']['arrival'] = {}
queries['eday']['arrival']['yes'] = Q(AA__gt=0)
queries['eday']['arrival']['no'] = Q(AA=0)|Q(AA__isnull=True)

queries['eday']['accreditation'] = {}
queries['eday']['accreditation']['complete'] = Q(BA__isnull=False) & Q(BA__lte=4) & Q(BB__isnull=False) & (Q(BC__gt=0)|Q(BC__isnull=False)) & Q(BD__isnull=False) & \
    Q(BE__isnull=False) & (Q(BF__gt=0)| Q(BF__isnull=False)) & Q(BG__isnull=False) & Q(BH__isnull=False) & Q(BJ__isnull=False) & (Q(BK__gt=0)|Q(BK__isnull=False)) & \
    Q(BM__isnull=False) & (Q(BN__gt=0)| Q(BN__isnull=False)) & Q(BP__isnull=False)
queries['eday']['accreditation']['partial'] = (Q(BA__isnull=False) | Q(BB__isnull=False) | (Q(BC__gt=0) & Q(BC__isnull=False)) | Q(BD__isnull=False) | \
    Q(BE__isnull=False) | (Q(BF__gt=0) & Q(BF__isnull=False)) | Q(BG__isnull=False) | Q(BH__isnull=False) | Q(BJ__isnull=False) | (Q(BK__gt=0) & Q(BK__isnull=False)) | \
    Q(BM__isnull=False) | (Q(BN__gt=0) & Q(BN__isnull=False)) | Q(BP__isnull=False)) & ~(queries['eday']['accreditation']['complete']) & ~Q(BA=5)
queries['eday']['accreditation']['not_open'] = Q(BA=5) & Q(BB__isnull=True) & (Q(BC=0)|Q(BC__isnull=True)) & Q(BD__isnull=True) & \
    Q(BE__isnull=True) & (Q(BF=0)|Q(BF__isnull=True)) & Q(BG__isnull=True) & Q(BH__isnull=True) & Q(BJ__isnull=True) & (Q(BK=0)|Q(BK__isnull=True)) & \
    Q(BM__isnull=True) & (Q(BN=0)|Q(BN__isnull=True)) & Q(BP__isnull=True)
queries['eday']['accreditation']['problem'] = Q(BA=5) & (Q(BB__isnull=False) | (Q(BC__gt=0)|Q(BC__isnull=False)) | Q(BD__isnull=False) | \
    Q(BE__isnull=False) | (Q(BF__gt=0)|Q(BF__isnull=False)) | Q(BG__isnull=False) | Q(BH__isnull=False) | Q(BJ__isnull=False) | Q(BK__gt=0) | \
    Q(BM__isnull=False) | (Q(BN__gt=0)|Q(BN__isnull=False)) | Q(BP__isnull=False))
queries['eday']['accreditation']['missing'] = Q(BA__isnull=True) & Q(BB__isnull=True) & (Q(BC=0)|Q(BC__isnull=True)) & Q(BD__isnull=True) & \
    Q(BE__isnull=True) & (Q(BF=0)|Q(BF__isnull=True)) & Q(BG__isnull=True) & Q(BH__isnull=True) & Q(BJ__isnull=True) & (Q(BK=0)|Q(BK__isnull=True)) & \
    Q(BM__isnull=True) & (Q(BN=0)|Q(BN__isnull=True)) & Q(BP__isnull=True)


queries['eday']['voting_and_counting'] = {}
queries['eday']['voting_and_counting']['complete'] = Q(CA__isnull=False) & Q(CB__gt=0) & Q(CC__isnull=False) & Q(CD__isnull=False) & \
    Q(CE__isnull=False) & Q(CF__gt=0) & Q(CG__gt=0) & Q(CH__gt=0) & Q(CJ__gt=0) & Q(CK__gt=0) & Q(CM__gt=0) & Q(CN__gt=0) & Q(CP__gt=0) & Q(CQ__gt=0)
queries['eday']['voting_and_counting']['partial'] = (Q(CA__isnull=False) | Q(CB__gt=0) | Q(CC__isnull=False) | \
    Q(CD__isnull=False) | Q(CE__isnull=False) | Q(CF__gt=0) | Q(CG__gt=0) | Q(CH__gt=0) | Q(CJ__gt=0) | Q(CK__gt=0) | \
    (Q(CM__gt=0)& Q(CM__isnull=False)) | Q(CN__gt=0) | Q(CP__gt=0) | Q(CQ__gt=0)) & ~(queries['eday']['voting_and_counting']['complete']) & ~Q(CA=5) & ~Q(BA=5)
queries['eday']['voting_and_counting']['not_open'] = (Q(CA=5) | Q(BA=5)) & (Q(CB=0)|Q(CB__isnull=True)) & Q(CC__isnull=True) & \
    Q(CD__isnull=True) & Q(CE__isnull=True) & (Q(CF=0)| Q(CF__isnull=True)) & (Q(CG=0)| Q(CG__isnull=True)) & \
    (Q(CH=0)| Q(CH__isnull=True)) & (Q(CJ=0)| Q(CJ__isnull=True)) & (Q(CK=0)| Q(CK__isnull=True)) & (Q(CM=0)| Q(CM__isnull=True)) & \
    (Q(CN=0)| Q(CN__isnull=True)) & (Q(CP=0)| Q(CP__isnull=True)) & (Q(CQ=0)| Q(CQ__isnull=True))
queries['eday']['voting_and_counting']['problem'] = (Q(CA=5) | Q(BA=5)) & (Q(CB__gt=0) | Q(CC__isnull=False) | Q(CD__isnull=False) | \
    Q(CE__isnull=False) | Q(CF__gt=0) | Q(CG__gt=0) | Q(CH__gt=0) | Q(CJ__gt=0) | Q(CK__gt=0) | \
    Q(CM__gt=0) | Q(CN__gt=0) | Q(CP__gt=0) | Q(CQ__gt=0))
queries['eday']['voting_and_counting']['missing'] = Q(CA__isnull=True) & (Q(CB=0)|Q(CB__isnull=True)) & Q(CC__isnull=True) & \
    Q(CD__isnull=True) & Q(CE__isnull=True) & (Q(CF=0)|Q(CF__isnull=True)) & (Q(CG=0)|Q(CG__isnull=True)) & (Q(CH=0)|Q(CH__isnull=True)) & \
    (Q(CJ=0)|Q(CJ__isnull=True)) & (Q(CK=0)|Q(CK__isnull=True)) & (Q(CM=0)|Q(CM__isnull=True)) & (Q(CN=0)|Q(CN__isnull=True)) & \
    (Q(CP=0)|Q(CP__isnull=True)) & (Q(CQ=0)|Q(CQ__isnull=True)) & ~Q(CA=5) & ~Q(BA=5)


queries['eday']['official_summary'] = {}
queries['eday']['official_summary']['complete'] = Q(DA__isnull=False) & Q(DB__isnull=False) & Q(DC__isnull=False) & Q(DD__isnull=False) & \
    Q(DE__isnull=False) & Q(DF__isnull=False) & Q(DG__isnull=False) & Q(DH__isnull=False)
queries['eday']['official_summary']['partial'] = (Q(DA__isnull=False) | Q(DB__isnull=False) | Q(DC__isnull=False) | Q(DD__isnull=False) | \
    Q(DE__isnull=False) | Q(DF__isnull=False) | Q(DG__isnull=False) | Q(DH__isnull=False)) & ~(queries['eday']['official_summary']['complete']) & ~Q(CA=5) & ~Q(BA=5)
queries['eday']['official_summary']['not_open'] = Q(DA__isnull=True) & Q(DB__isnull=True) & Q(DC__isnull=True) & Q(DD__isnull=True) & \
    Q(DE__isnull=True) & Q(DF__isnull=True) & Q(DG__isnull=True) & Q(DH__isnull=True) & (Q(CA=5) | Q(BA=5))
queries['eday']['official_summary']['problem'] = (Q(DA__isnull=False) | Q(DB__isnull=False) | Q(DC__isnull=False) | Q(DD__isnull=False) | \
    Q(DE__isnull=False) | Q(DF__isnull=False) | Q(DG__isnull=False) | Q(DH__isnull=False)) & (Q(CA=5) | Q(BA=5))
queries['eday']['official_summary']['missing'] = Q(DA__isnull=True) & Q(DB__isnull=True) & Q(DC__isnull=True) & Q(DD__isnull=True) & \
    Q(DE__isnull=True) & Q(DF__isnull=True) & Q(DG__isnull=True) & Q(DH__isnull=True) & ~Q(CA=5) & ~Q(BA=5)


queries['eday']['official_results'] = {}
queries['eday']['official_results']['complete'] = Q(sms_status_5th=1) & ~Q(BA=5) & ~Q(CA=5)
queries['eday']['official_results']['partial'] = Q(sms_status_5th=2) & ~Q(CA=5) & ~Q(BA=5)
queries['eday']['official_results']['not_open'] = Q(sms_status_5th=3) & (Q(CA=5) | Q(BA=5))
queries['eday']['official_results']['problem'] = (Q(sms_status_5th=1) | Q(sms_status_5th=2)) & (Q(CA=5) | Q(BA=5))
queries['eday']['official_results']['missing'] = Q(sms_status_5th=3) & ~Q(CA=5) & ~Q(BA=5)

queries['eday']['stations'] = {}
queries['eday']['stations']['complete'] = Q(AA__gt=0) & Q(BA__isnull=False) & Q(BB__isnull=False) & (Q(BC__gt=0)|Q(BC__isnull=False)) & Q(BD__isnull=False) & \
    Q(BE__isnull=False) & (Q(BF__gt=0)| Q(BF__isnull=False)) & Q(BG__isnull=False) & Q(BH__isnull=False) & Q(BJ__isnull=False) & (Q(BK__gt=0)|Q(BK__isnull=False)) & \
    Q(BM__isnull=False) & (Q(BN__gt=0)| Q(BN__isnull=False)) & Q(BP__isnull=False) & Q(CA__isnull=False) & Q(CB__gt=0) & Q(CC__isnull=False) & Q(CD__isnull=False) & \
    Q(CE__isnull=False) & Q(CF__gt=0) & Q(CG__gt=0) & Q(CH__gt=0) & Q(CJ__gt=0) & Q(CK__gt=0) & Q(CM__gt=0) & Q(CN__gt=0) & Q(CP__gt=0) & Q(CQ__gt=0) & \
    Q(DA__isnull=False) & Q(DB__isnull=False) & Q(DC__isnull=False) & Q(DD__isnull=False) & Q(DE__isnull=False) & Q(DF__isnull=False) & Q(DG__isnull=False) & \
    Q(DH__isnull=False) & Q(sms_status_5th=1)
queries['eday']['stations']['partial'] = Q(AA__gt=0) | Q(BA__isnull=False) | Q(BB__isnull=False) | (Q(BC__gt=0)|Q(BC__isnull=False)) | Q(BD__isnull=False) | \
        Q(BE__isnull=False) | (Q(BF__gt=0)| Q(BF__isnull=False)) | Q(BG__isnull=False) | Q(BH__isnull=False) | Q(BJ__isnull=False) | (Q(BK__gt=0)|Q(BK__isnull=False)) | \
        Q(BM__isnull=False) | (Q(BN__gt=0)| Q(BN__isnull=False)) | Q(BP__isnull=False) | Q(CA__isnull=False) | Q(CB__gt=0) | Q(CC__isnull=False) | Q(CD__isnull=False) | \
        Q(CE__isnull=False) | Q(CF__gt=0) | Q(CG__gt=0) | Q(CH__gt=0) | Q(CJ__gt=0) | Q(CK__gt=0) | Q(CM__gt=0) | Q(CN__gt=0) | Q(CP__gt=0) | Q(CQ__gt=0) | \
        Q(DA__isnull=False) | Q(DB__isnull=False) | Q(DC__isnull=False) | Q(DD__isnull=False) | Q(DE__isnull=False) | Q(DF__isnull=False) | Q(DG__isnull=False) | \
        Q(DH__isnull=False) | Q(sms_status_5th=1) & ~(queries['eday']['stations']['complete'])
queries['eday']['stations']['missing'] = Q(AA=0)|Q(AA__isnull=True) & Q(BA__isnull=True) & Q(BB__isnull=True) & (Q(BC=0)|Q(BC__isnull=True)) & Q(BD__isnull=True) & \
            Q(BE__isnull=True) & (Q(BF=0)|Q(BF__isnull=True)) & Q(BG__isnull=True) & Q(BH__isnull=True) & Q(BJ__isnull=True) & (Q(BK=0)|Q(BK__isnull=True)) & \
            Q(BM__isnull=True) & (Q(BN=0)|Q(BN__isnull=True)) & Q(BP__isnull=True) & Q(CA__isnull=True) & (Q(CB=0)|Q(CB__isnull=True)) & Q(CC__isnull=True) & \
            Q(CD__isnull=True) & Q(CE__isnull=True) & (Q(CF=0)|Q(CF__isnull=True)) & (Q(CG=0)|Q(CG__isnull=True)) & (Q(CH=0)|Q(CH__isnull=True)) & \
            (Q(CJ=0)|Q(CJ__isnull=True)) & (Q(CK=0)|Q(CK__isnull=True)) & (Q(CM=0)|Q(CM__isnull=True)) & (Q(CN=0)|Q(CN__isnull=True)) & \
            (Q(CP=0)|Q(CP__isnull=True)) & (Q(CQ=0)|Q(CQ__isnull=True)) & Q(DA__isnull=True) & Q(DB__isnull=True) & Q(DC__isnull=True) & Q(DD__isnull=True) & \
            Q(DE__isnull=True) & Q(DF__isnull=True) & Q(DG__isnull=True) & Q(DH__isnull=True) & Q(sms_status_5th=3)