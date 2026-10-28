// Lightweight glTF geometry preview renderer. Input is prepared directly from
// the GLB by render_preview.py. The background and ground are preview only.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <vector>
#include <string>
using namespace std;
struct V {double x,y,z; V operator+(V o)const{return{x+o.x,y+o.y,z+o.z};} V operator-(V o)const{return{x-o.x,y-o.y,z-o.z};} V operator*(double s)const{return{x*s,y*s,z*s};}};
double dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;} V cross(V a,V b){return{a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
V unit(V a){double l=sqrt(dot(a,a));return a*(1.0/max(l,1e-15));}
struct Tex{uint32_t w,h,flags;vector<uint8_t> data;};
struct Point{float x,y,z,u,v;}; struct Tri{uint32_t mat; Point p[3];};
struct Screen{double x,y,z, iz,u,v;};
static inline double edge(double ax,double ay,double bx,double by,double x,double y){return (x-ax)*(by-ay)-(y-ay)*(bx-ax);}
int main(int argc,char **argv){
 if(argc!=11){cerr<<"Usage: renderer input output ex ey ez tx ty tz fov degrees\n";return 1;}
 ifstream in(argv[1],ios::binary); if(!in){cerr<<"bad input\n";return 2;}
 char magic[4];uint32_t W,H,nm,nt;in.read(magic,4);in.read((char*)&W,4);in.read((char*)&H,4);in.read((char*)&nm,4);in.read((char*)&nt,4);
 if(string(magic,4)!="SHED"){cerr<<"bad header\n";return 3;}
 vector<Tex> tex(nm);for(auto &t:tex){in.read((char*)&t.w,4);in.read((char*)&t.h,4);in.read((char*)&t.flags,4);t.data.resize(t.w*t.h*4);in.read((char*)t.data.data(),t.data.size());}
 vector<Tri> tri(nt);in.read((char*)tri.data(),nt*sizeof(Tri)); if(!in){cerr<<"truncated mesh\n";return 4;}
 V eye{stod(argv[3]),stod(argv[4]),stod(argv[5])}, target{stod(argv[6]),stod(argv[7]),stod(argv[8])};double fov=stod(argv[9]);int repeat=stoi(argv[10]);
 V forward=unit(target-eye), right=unit(cross(forward,{0,1,0})), up=unit(cross(right,forward));double focal=H/(2*tan(fov*3.141592653589793/360.0));
 vector<float> rgb((size_t)W*H*3), depth((size_t)W*H,1e25f);
 // Neutral studio and an analytic ground plane; this is not exported geometry.
 for(int y=0;y<(int)H;y++)for(int x=0;x<(int)W;x++){
  size_t k=(size_t)y*W+x;double sy=(double)y/H;float c=(float)(.83-.12*sy);rgb[3*k]=c*.98f;rgb[3*k+1]=c;rgb[3*k+2]=c*1.015f;
  V ray=forward+right*((x-W/2.0)/focal)+up*((H/2.0-y)/focal); double t=(-.035-eye.y)/ray.y;
  if(t>0){V hit=eye+ray*t;float shade=.78f;
   // Small soft foot shadows mark where the geometry meets the preview floor.
   for(int n=0;n<repeat;n++)for(int s=-1;s<=1;s+=2){double dx=hit.x-s*9.7,dz=hit.z-(n*6+.29);shade-=.14f*(float)exp(-(dx*dx+dz*dz)/1.5);}
   double gx=abs(hit.x-round(hit.x/5)*5),gz=abs(hit.z-round(hit.z/5)*5); if(gx<.018||gz<.018)shade-=.025f;
   rgb[3*k]=shade*.98f;rgb[3*k+1]=shade*.99f;rgb[3*k+2]=shade*.97f;depth[k]=(float)t;
  }
 }
 vector<Screen> screen(3);V light=unit({-.45,.85,-.50}), fill=unit({.7,.55,.8});
 // All opaque faces first, glass after. Transparent fragments blend only where
 // they are nearer than the opaque z-buffer; the glass group is back-to-front.
 vector<int> order;order.reserve(nt);for(int pass=0;pass<2;pass++){
  order.clear();for(uint32_t i=0;i<nt;i++)if(((tex[tri[i].mat].flags&1)!=0)==(pass==1))order.push_back(i);
  if(pass){sort(order.begin(),order.end(),[&](int a,int b){V ca{0,0,0},cb{0,0,0};for(int j=0;j<3;j++){ca=ca+V{tri[a].p[j].x,tri[a].p[j].y,tri[a].p[j].z};cb=cb+V{tri[b].p[j].x,tri[b].p[j].y,tri[b].p[j].z};}return dot(ca-eye*3,forward)>dot(cb-eye*3,forward);});}
  for(int ti:order){const Tri &t=tri[ti];const Tex &texture=tex[t.mat];V pts[3];bool bad=false;
   for(int i=0;i<3;i++){pts[i]={t.p[i].x,t.p[i].y,t.p[i].z};V q=pts[i]-eye;double z=dot(q,forward);if(z<.05){bad=true;break;}
    screen[i]={W/2.0+focal*dot(q,right)/z,H/2.0-focal*dot(q,up)/z,z,1/z,t.p[i].u,t.p[i].v};}
   if(bad)continue;const Screen &a=screen[0],&b=screen[1],&c=screen[2];
   double area=edge(a.x,a.y,b.x,b.y,c.x,c.y);if(abs(area)<1e-8)continue;
   int xmin=max(0,(int)floor(min({a.x,b.x,c.x}))),xmax=min((int)W-1,(int)ceil(max({a.x,b.x,c.x})));
   int ymin=max(0,(int)floor(min({a.y,b.y,c.y}))),ymax=min((int)H-1,(int)ceil(max({a.y,b.y,c.y})));if(xmin>xmax||ymin>ymax)continue;
   V n=unit(cross(pts[1]-pts[0],pts[2]-pts[0]));if(dot(n,eye-pts[0])<0)n=n*(-1);
   double illumination=.62+.56*max(0.0,dot(n,light))+.18*max(0.0,dot(n,fill)); if(texture.flags&2)illumination=1.35;
   if(texture.flags&1)illumination=1.0;
   for(int y=ymin;y<=ymax;y++)for(int x=xmin;x<=xmax;x++){
    double px=x+.5,py=y+.5;double wa=edge(b.x,b.y,c.x,c.y,px,py)/area,wb=edge(c.x,c.y,a.x,a.y,px,py)/area,wc=1-wa-wb;
    if(wa<-.000001||wb<-.000001||wc<-.000001)continue;double iz=wa*a.iz+wb*b.iz+wc*c.iz;if(iz<=0)continue;double z=1/iz;
    size_t k=(size_t)y*W+x;if(z>=depth[k]-.00001)continue;
    double u=(wa*a.u*a.iz+wb*b.u*b.iz+wc*c.u*c.iz)*z,v=(wa*a.v*a.iz+wb*b.v*b.iz+wc*c.v*c.iz)*z;
    u-=floor(u);v-=floor(v);int ix=min((int)texture.w-1,(int)(u*texture.w)),iy=min((int)texture.h-1,(int)(v*texture.h));size_t ix4=4*((size_t)iy*texture.w+ix);
    float alpha=(texture.flags&1)?texture.data[ix4+3]/255.0f:1;
    for(int channel=0;channel<3;channel++){float src=min(1.0,texture.data[ix4+channel]/255.0*illumination);rgb[3*k+channel]=src*alpha+rgb[3*k+channel]*(1-alpha);}
    if(!(texture.flags&1))depth[k]=(float)z;
   }
  }
 }
 ofstream out(argv[2],ios::binary);out<<"P6\n"<<W<<" "<<H<<"\n255\n";for(float v:rgb){uint8_t b=(uint8_t)(max(0.f,min(1.f,v))*255+.5f);out.write((char*)&b,1);}cerr<<"rendered "<<nt<<" actual GLB triangles, "<<W<<"x"<<H<<"\n";
}
