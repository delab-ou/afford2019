from pathlib import Path;
import sys;
import subprocess;

def genPromelaHeader(nodes=4,around=1,rtlen=2,retry=1):
    return "\
#define AROUND "+str(around)+"\n\
#define CHAN_BUF 1\n\
#define NODES "+str(nodes)+"\n\
#define RT_LENGTH "+str(rtlen)+"\n\
#define RETRY "+str(retry)+"\n\
typedef entry{byte seq,dest,next,hops};\n\
typedef table{entry entries[RT_LENGTH]};\n\
typedef packet{byte type,src,dest,sndr,next,hops, seq};\n\
chan c[NODES] = [CHAN_BUF] of {packet};\n\
table tables[NODES];\n\
c_decl{\n\
\#include \"replace.h\"\n\
\#include \"print_state.h\"\n\
};\n\
";
def genBroadcast(nodes=4):
    ret= "\
inline broadcast(){\n\
\tatomic{\n\
\t\tfor(cnt: 1 .. AROUND){\n\
\t\t\tif\n";
    for x in range(nodes):
        ret+="\t\t\t\t::next="+str(x)+";\n"
    ret+="\
\t\t\t\t::next=255;\n\
\t\t\tfi;\n\
\t\t\tif::((next==255) || ((next+1)==id))->skip;\n\
\t\t\t\t::else -> unicast(next);\n\
\t\t\tfi;\n\
\t\t};\n\
\t\tnext=0;\n\
\t};\n\
}";
    return ret;


def genNODES():
    file=Path('./aodv_node_src');
    ret="";
    with file.open() as f:
        ret=f.read();
    return ret;

def genInit(nodes=4):
    ret="\
init{\n\
\tatomic{\n\
\t\trun Src(1,2);\n\
\t\trun Dest(2);\n"
    for x in range(nodes-2):
        ret+="\t\trun Node("+str(x+3)+");\n";
    ret+="\
\t}\n\
}";
    return ret;

def genQfunc(nodes=4):
    ret3="";
    ret2="";
    ret1="\
void (*moveq[])(int *perm, Q0 *_now, Q0 *_tmp)={\n"
    for i in range(3,(nodes+1)):
        for j in range(3,(nodes+1)):
            ret1+="moveQ"+str(i)+"Q"+str(j);
            ret2+=genQreplace(i,j);
            ret3+=genQreplaceDefinition(i,j)+";\n";
            if not(i==nodes and j==nodes):
                ret1+=",";
    ret1+="};"
    return ret1,ret2,ret3;
def genQreplaceDefinition(now=0,tmp=0):
    return "void moveQ"+str(now)+"Q"+str(tmp)+"(int *perm, Q0 *_now, Q0 *_tmp)";

def genQreplace(now=0,tmp=0):
    ret=genQreplaceDefinition(now,tmp);
    if (now==tmp):
        return ret+"{}";

    ret+="\
{\n\
  Q"+str(now)+" *_nowQ=(Q"+str(now)+"*)_now;\n\
  Q"+str(tmp)+" *_tmpQ=(Q"+str(tmp)+"*)_tmp;\n\
  _tmpQ->Qlen=_nowQ->Qlen;\n\
  _tmpQ->contents[0].fld0=_nowQ->contents[0].fld0;\n\
  _tmpQ->contents[0].fld1=_nowQ->contents[0].fld1;\n\
  _tmpQ->contents[0].fld2=_nowQ->contents[0].fld2;\n\
  _tmpQ->contents[0].fld3=_nowQ->contents[0].fld3;\n\
  _tmpQ->contents[0].fld4=_nowQ->contents[0].fld4;\n\
  _tmpQ->contents[0].fld5=_nowQ->contents[0].fld5;\n\
  _tmpQ->contents[0].fld6=_nowQ->contents[0].fld6;\n\
  if((3 <= _tmpQ->contents[0].fld3) && (_tmpQ->contents[0].fld3 <= NODES)){\n\
    _tmpQ->contents[0].fld3=perm[_tmpQ->contents[0].fld3-3];\n\
  }\n\
  if((3 <= _tmpQ->contents[0].fld4) && (_tmpQ->contents[0].fld4 <= NODES)){\n\
    _tmpQ->contents[0].fld4=perm[_tmpQ->contents[0].fld4-3];\n\
  }\n\
}\n";
    return ret;

def genReplaceHeader(nodes=4,rtlen=2):
    return '\
#ifndef REPLACE_H\n\
#define REPLACE_H\n\
#include "pan.h"\n\
#include "print_state.h"\n\
#ifndef NODES\n\
#define NODES '+str(nodes)+'\n\
#endif\n\
#ifndef RT_LENGTH\n\
#define RT_LENGTH '+str(rtlen)+'\n\
#endif\n\
#define STORED_TOPO 100\n\
struct table topo['+str(nodes*2-1)+'][STORED_TOPO][NODES];\n\
int entries['+str(nodes*2-1)+'];\n';

def genReplace(nodes=4,rtlen=2):

    fileS=Path('./replace_src');
    file_code=Path("./replace.c");
    file_header=Path("./replace.h");

    ret='\
#include <stdio.h>\n\
#include <string.h>\n\
#include "replace.h"\n';
    qp,qf,qd=genQfunc(nodes);
    ret+=qp+"\n";
    ret+=qf+"\n";

    with fileS.open() as f:
        ret+=f.read();
    with file_code.open('w') as f:
        f.write(ret);
    ret=genReplaceHeader(nodes,rtlen);
    ret+=qd+"\n";
    ret+="\
void moveQueue(int *perm, Q0* _now, Q0* _tmp);\n\
void moveDestQ(int *perm, Q2 *q);\n\
void moveSrcQ(int *perm, Q1 *q);\n\
int isSameState(char* s1,char *s2, int size);\n\
void movePacketSenderAndNext(int *perm, struct packet *_tmp);\n\
void movePacket(int*perm, struct packet *_now, struct packet *_tmp);\n\
void movePackets(int *perm, P2 *_now, P2 *_tmp);\n\
void moveSrcPackets(int *perm, P0* _tmp);\n\
void moveDestPackets(int *perm, P1* _tmp);\n\
void moveProcess(int *perm, P2 *_now, P2* _tmp);\n\
int countEntries(struct table *t);\n\
void moveEntryNext(int *perm, struct entry *_now, struct entry *_tmp);\n\
void moveEntry(struct entry *_now, struct entry *_tmp);\n\
void moveTable(int *perm, struct table *_now,struct table *_tmp);\n\
void moveSrcDestEntry(int *perm, struct entry *_e);\n\
void moveSrcDestTable(int *perm, struct table *t);\n\
void moveState(int *perm, struct State *_now,struct State *_tmp,int id,short *pos,short *qos);\n\
void replace(int *perm, struct State *_now, struct State* _tmp,short *pos,short *qos);\n\
int isSameEntry(struct entry *_now, struct entry *_tmp);\n\
int isSameTable(struct table *_now,struct table* _tmp);\n\
int isSameTables(struct table *_now,struct table *_tmp);\n\
void countTopologies(struct State *s);\n\
#endif"
    with file_header.open('w') as f:
        f.write(ret);
    return ret;

def genPrintQDefinition(id):
    return 'void pq'+str(id)+'(Q0* q0,int id)';

def genPrintQueueCode(id):
    ret=genPrintQDefinition(id)+'{\n';
    ret+='Q'+str(id)+' *q= (Q'+str(id)+'*) q0;\n';
    ret+='printf("Q%d:Qlen=%d,_t=%d\\n",id,q->Qlen,q->_t);\n\
    printf("(%d,%d,%d,%d,%d,%d,%d)\\n",\n\
    q->contents[0].fld0,\n\
    q->contents[0].fld1,\n\
    q->contents[0].fld2,\n\
    q->contents[0].fld3,\n\
    q->contents[0].fld4,\n\
    q->contents[0].fld5,\n\
    q->contents[0].fld6\n\
  );\n\
}\n';
    return ret;

def genPrintQueue(nodes=4):
    ret1="";
    ret2="";
    ret3="void (*pq[])(Q0 *q,int id)={";
    for i in range(1,nodes+1):
        ret1+=genPrintQDefinition(i)+';\n';
        ret2+=genPrintQueueCode(i);
        ret3+='pq'+str(i);
        if not(i==nodes):
            ret3+=',';
    ret3+='};\n';
    return ret1,ret2,ret3;

def genPrintHeader(nodes=4, rtlen=2):
    return '\
#ifndef STATE_PRINT_H\n\
#define STATE_PRINT_H\n\
#include "pan.h"\n\
#include "replace.h"\n';

def genPrintTopologies(nodes=4):

    ret='void printTopologies(){\n\
    printf("entries:%d, 0:%d';
    values='entries[0]';

    for i in range(1,nodes*2-1):
        ret+=','+str(i)+':%d';
        values+=',entries['+str(i)+']';
    ret+='\\n",';
    return ret+'totalEntry(),'+values+');\n}'


def genPrintCode(nodes=4,rtlen=2):
    fileS=Path('./print_src');
    file_code=Path('./print_state.c');
    file_header=Path('./print_state.h');

    qd,qc,qf=genPrintQueue(nodes);

    ret='#include <stdio.h>\n\
#include <string.h>\n\
#include "replace.h"\n\
#include "print_state.h"\n';
    ret+=qf;
    ret+=qc;
    with fileS.open() as f:
        ret+=f.read();
    with file_code.open('w') as f:
        f.write(ret);
        f.write(genPrintTopologies(nodes));

    ret=genPrintHeader(nodes,rtlen);
    ret+=qd;
    ret+='\
void printQueue(struct State*,short*,int);\n\
void printAllQueue(struct State*,short*);\n\
void printEntry(struct table*,int);\n\
void printTable(struct table*,int,int);\n\
void printPacket(struct packet*);\n\
void printProcessP0(struct P0*);\n\
void printProcessP1(struct P1*);\n\
void printProcessP2(struct P2*);\n\
void printProcesses(struct State*, short*);\n\
void printState(struct State* ,short*, short*);\n\
void printDifferences(char*,char*,int);\n\
int totalEntry();\n\
void printTopologies();\n\
void printTopologiesInDetail();\n\
';
    ret+='#endif\n';
    with file_header.open('w') as f:
        f.write(ret);

def avoidTheSame(a,i):
    ret="";
    if (i>=2):
        ret+="("+a[0]+"!="+a[i-1]+")"
        for l in range(1,i-1):
            ret+="&&("+a[l]+"!="+a[i-1]+")";
    return ret;

def constraint(a,v,i):
    c=avoidTheSame(a,i);
    return "("+a[i]+"<="+str(v)+")"+("&&" if c!="" else "")+c;

def avoidTheSameNode(a,nodes):
    ret="("+a[0]+"!=3)";
    for l in range(4,nodes+1):
        ret+="||("+a[l-3]+"!="+str(l)+")"
    return "("+ret+")";

def createReplaceCode(nodes=4):
    loops=["l"+str(i+1) for i in range(2,nodes)];

    cr="  ";
    ret="\
struct State tmp_state;\n\
static int ce=0;\n\
int counter=countEntries(now.tables);\n\
if(ce<counter){\n\
	ce=counter;\n\
}\n\
if(ce=="+str(nodes*2-2)+"){\n\
memcpy(&tmp_state,&now,now._vsz);\n\
int found=0;\n\
";
    ret+="int "+loops[0]+"=0";
    for i in range(1,nodes-2):
        ret+=","+loops[i]+"=0"
    ret+=";\n";
    ret+="int permutation["+str(nodes-2)+"];\n";

    for i in range(nodes-2):
        it1="for ("+loops[i]+" = 3;";
        it2="&&(found==0);"+loops[i]+"++){\n";
        ret+=it1+constraint(loops,nodes,i)+it2;
        ret+="permutation["+str(i)+"]="+loops[i]+";\n"
    ret+="if("+avoidTheSame(loops,nodes-2)+"&&"+avoidTheSameNode(loops,nodes)+"){\n"
    ret+="replace(permutation,&now,&tmp_state,proc_offset,q_offset);\n";
    ret+="int tmp_n=compress(((char*)&tmp_state),tmp_state._vsz);\n";
    ret+="s_hash((uchar *)v,tmp_n);\n";
    ret+="tmp=H_tab[j1_spin];\n";
    ret+="if(tmp){\n";
    ret+="int tmp_m=memcmp(((char *)&(tmp->state)) ,v,tmp_n);\n";
    ret+="if(!tmp_m){\n";
    ret+="vin=(char*)&tmp_state;\n";
    ret+="found=1;\n"
    ret+="}\n"
    ret+="}\n"
    ret+="}\n"
    ret+="}\n";
    for i in range(nodes-2):
        ret+="}\n";
    return ret;

def genInsertingCode(nodes=4):
    filePAN=Path('./pan.c');
    filePAN2=Path('./pan_symm.c');
    hstore=0;
    compress=0;
    with filePAN2.open('w') as of:
        with filePAN.open() as f:
            line=f.readline();
            while line:
                if "h_store(char *vin, int nin)" in line:
                    hstore=1;
                if "n = compress(vin, nin);" in line and hstore==1:
                    compress+=1;
                    of.write(createReplaceCode(nodes));
                of.write(line);
                line=f.readline();

def genPromelaCode(nodes=4,around=1,rtlen=2,retry=1):
    file_pml=Path('./aodv_gen.pml');
    ret=genPromelaHeader(nodes,around,rtlen,retry)+"\n"+\
    genBroadcast(nodes)+"\n"+\
        genNODES()+"\n"+\
        genInit(nodes);
    with file_pml.open('w') as f:
        f.write(ret);

def genPromelaCsource(nodes=4,around=1,rtlen=2,retry=1):
    genPromelaCode(nodes,around,rtlen,retry);
    subprocess.check_output(['spin','-a','aodv_gen.pml'])
    genReplace(nodes,rtlen);
    genInsertingCode(nodes);
    genPrintCode(nodes,rtlen);
    suffix="n"+str(nodes)+"a"+str(around)+"r"+str(rtlen)+"r"+str(retry);
    #subprocess.check_output(['gcc','-DNOREDUCE','-o','po-'+suffix,'pan.c','replace_automated.c','print_automated.c'])
    #subprocess.check_output(['gcc','-DNOREDUCE','-o','pa-'+suffix,'pan_automated.c','replace_automated.c','print_automated.c'])


genPromelaCsource(5,1,2,1);
