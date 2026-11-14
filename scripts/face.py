import cv2,json,numpy as np,sys
cap=cv2.VideoCapture(sys.argv[1]); fps=cap.get(5); n=int(cap.get(7))
cc=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
pc=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_profileface.xml")
pts=[];i=0
while True:
    ok,f=cap.read()
    if not ok:break
    if i%6==0:
        g=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY); g=g[:int(g.shape[0]*0.6)]
        best=None
        for c in (cc,pc):
            for flip in (False,True) if c is pc else (False,):
                gg=cv2.flip(g,1) if flip else g
                for (x,y,w,h) in c.detectMultiScale(gg,1.1,5,minSize=(40,40)):
                    if flip:x=g.shape[1]-x-w
                    if best is None or w>best[2]:best=(x,y,w,h)
            if best is not None:break
        if best is not None:
            x,y,w,h=best; pts.append((i/fps,(x+w/2)/f.shape[1],(y+h/2)/f.shape[0],w/f.shape[1]))
    i+=1
json.dump(pts,open(sys.argv[2],"w"))
print(len(pts),n)
