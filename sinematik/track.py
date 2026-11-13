import cv2, numpy as np, sys
CW=243
def track(src,a,b,step=0.5):
    cap=cv2.VideoCapture(src); xs=[]; ts=[]; t=a
    while t<b:
        cap.set(cv2.CAP_PROP_POS_MSEC,t*1000); ok,fr=cap.read()
        if not ok: break
        hsv=cv2.cvtColor(fr,cv2.COLOR_BGR2HSV)
        reg=hsv[200:380,:,:]
        m=((reg[:,:,0]>95)&(reg[:,:,0]<135)&(reg[:,:,1]>45)&(reg[:,:,2]<140)).astype(np.float32)  # navy robe only
        col=m.sum(0); col[:60]=0; col[-60:]=0
        if col.sum()>500:
            xs.append(float((col*np.arange(768)).sum()/col.sum())); ts.append(t-a)
        t+=step
    if not xs: return [(0.0,(768-CW)/2)]
    sm=[float(np.median(xs[max(0,i-3):i+4])) for i in range(len(xs))]
    kf=[]
    for t,x in zip(ts,sm):
        cx=min(max(x-CW/2,0),768-CW)
        if not kf or abs(cx-kf[-1][1])>10: kf.append((round(t,2),round(cx,1)))
    return kf
if __name__=="__main__":
    print(track(sys.argv[1],float(sys.argv[2]),float(sys.argv[3])))
