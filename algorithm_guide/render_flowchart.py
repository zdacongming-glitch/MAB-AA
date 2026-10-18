"""Render this guide's canonical Mermaid nodes/edges into a readable PNG/PDF.

The layout is fixed; labels and directed edges are read from fccp_flowchart.md.
This small purpose-built renderer avoids a browser or a JavaScript dependency.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
COLORS = {
    'neutral': ('#f3f4f6', '#6b7280', '#1f2937'),
    'decision': ('#fef9c3', '#ca8a04', '#713f12'),
    'certificate': ('#ffedd5', '#ea580c', '#7c2d12'),
    'reward': ('#dbeafe', '#2563eb', '#1e3a5f'),
    'shared': ('#dcfce7', '#16a34a', '#14532d'),
    'positive_label': ('#dcfce7', '#16a34a', '#14532d'),
    'negative_label': ('#fee2e2', '#dc2626', '#7f1d1d'),
    'pending': ('#fef9c3', '#ca8a04', '#713f12'),
    'paused_label': ('#f3f4f6', '#6b7280', '#1f2937'),
    'active_work': ('#ffedd5', '#ea580c', '#7c2d12'),
}

LAYOUT = {
    'arrivals': (660,290,1100,140),
    'cert_enabled': (435,520,610,155),
    'cert_plan': (435,715,650,135),
    'phase_ready': (435,900,430,115),
    'cert_budget': (435,1080,610,170),
    'cert_action': (435,1285,650,100),
    'reward_action': (1060,1190,430,230),
    'actual_pull': (660,1465,1000,140),
    'all_reports': (660,1630,1000,135),
    'gap_bounds': (1640,310,540,115),
    'positive': (1640,485,540,115),
    'negative': (1640,650,540,115),
    'unresolved': (1640,815,540,115),
    'paused': (1640,1080,540,125),
    'work_set': (1640,1260,540,125),
}

ROUTES = {
    ('arrivals','cert_enabled'): [(660,360),(660,400),(435,400),(435,442.5)],
    ('cert_enabled','cert_plan'): [(435,597.5),(435,647.5)],
    ('cert_enabled','reward_action'): [(740,520),(1060,520),(1060,1075)],
    ('cert_plan','phase_ready'): [(435,782.5),(435,842.5)],
    ('phase_ready','cert_budget'): [(435,957.5),(435,995)],
    ('phase_ready','reward_action'): [(650,900),(815,900),(815,1130),(845,1130)],
    ('cert_budget','cert_action'): [(435,1165),(435,1235)],
    ('cert_budget','reward_action'): [(740,1080),(770,1080),(770,1250),(845,1250)],
    ('cert_action','actual_pull'): [(435,1335),(435,1365),(660,1365),(660,1395)],
    ('reward_action','actual_pull'): [(1060,1305),(1060,1365),(660,1365),(660,1395)],
    ('actual_pull','all_reports'): [(660,1535),(660,1562.5)],
    ('all_reports','arrivals'): [(660,1697.5),(660,1750),(70,1750),(70,290),(110,290)],
    ('gap_bounds','positive'): [(1640,367.5),(1640,395),(1345,395),(1345,485),(1370,485)],
    ('gap_bounds','negative'): [(1640,367.5),(1640,395),(1345,395),(1345,650),(1370,650)],
    ('gap_bounds','unresolved'): [(1640,367.5),(1640,395),(1345,395),(1345,815),(1370,815)],
    ('unresolved','paused'): [(1640,872.5),(1640,925),(1345,925),(1345,1080),(1370,1080)],
    ('unresolved','work_set'): [(1640,872.5),(1640,925),(1345,925),(1345,1260),(1370,1260)],
}

LABEL_POSITIONS = {
    ('cert_enabled','cert_plan'): (465,620),
    ('cert_enabled','reward_action'): (850,490),
    ('phase_ready','cert_budget'): (465,975),
    ('phase_ready','reward_action'): (735,870),
    ('cert_budget','cert_action'): (475,1200),
    ('cert_budget','reward_action'): (775,1185),
    ('all_reports','arrivals'): (360,1722),
}


def parse(source):
    blocks = re.findall(r'```mermaid\s*\n(.*?)```', source, re.S)
    assert len(blocks) == 2
    nodes, classes, edges = {}, {}, {}
    for block in blocks:
        assert 'accTitle:' in block and 'accDescr:' in block
        for line in block.splitlines():
            m = re.match(r'^\s*([a-z_]+)(?:\["([^"]*)"\]|\{"([^"]*)"\})\s*$', line)
            if m:
                nodes[m[1]] = (re.sub(r'<br\s*/?>','\n',m[2] if m[2] is not None else m[3]), bool(m[3]))
            m = re.match(r'^\s*([a-z_]+)\s*-->(?:\|([^|]+)\|)?\s*([a-z_]+)\s*$',line)
            if m:
                edges[(m[1],m[3])] = m[2]
            m = re.match(r'^\s*class\s+([a-z_,]+)\s+([a-z_]+)\s*$',line)
            if m:
                for name in m[1].split(','):
                    classes[name] = m[2]
    assert set(nodes) == set(LAYOUT)
    assert set(edges) == set(ROUTES), (set(edges)-set(ROUTES),set(ROUTES)-set(edges))
    assert set(classes) == set(nodes)
    return nodes, classes, edges


def render(font_path):
    source = (ROOT/'fccp_flowchart.md').read_text(encoding='utf-8')
    nodes, classes, edges = parse(source)
    img = Image.new('RGB',(2000,1880),'#ffffff')
    draw = ImageDraw.Draw(img)
    def font(size):
        return ImageFont.truetype(str(font_path),size)
    def centered(text, x, y, size=27, color='#172033', width=None, height=None):
        while True:
            f=font(size)
            b=draw.multiline_textbbox((0,0),text,font=f,spacing=10,align='center')
            if (width is None or b[2]-b[0]<=width) and (height is None or b[3]-b[1]<=height):
                break
            size-=1
            if size<15:
                raise RuntimeError('Node text will not fit: '+text)
        draw.multiline_text((x-(b[2]-b[0])/2-b[0],y-(b[3]-b[1])/2-b[1]),text,font=f,fill=color,spacing=10,align='center')
    def arrow(points):
        draw.line(points,fill='#576273',width=4,joint='curve')
        x,y=points[-1]; x0,y0=points[-2]
        angle=math.atan2(y-y0,x-x0)
        back=(x-15*math.cos(angle),y-15*math.sin(angle))
        perp=(-6*math.sin(angle),6*math.cos(angle))
        draw.polygon([(x,y),(back[0]+perp[0],back[1]+perp[1]),(back[0]-perp[0],back[1]-perp[1])],fill='#576273')

    draw.text((65,35),'F-CCP：每轮怎样选臂、怎样分类',font=font(49),fill='#12233f')
    draw.text((68,108),'认证与收益是两种选臂理由；所有观测共用一套统计量，每轮只拉一次臂。',font=font(26),fill='#566172')
    draw.rounded_rectangle((40,170,1290,1790),radius=24,fill='#ffffff',outline='#d5dce5',width=3)
    draw.rounded_rectangle((1320,170,1960,1790),radius=24,fill='#ffffff',outline='#d5dce5',width=3)
    draw.text((85,190),'① 选臂 → 一次观测 → 更新报告',font=font(28),fill='#12233f')
    draw.text((1360,190),'② 对每个臂重新分类',font=font(28),fill='#12233f')

    for edge in edges:
        arrow(ROUTES[edge])
    for name,(text,diamond) in nodes.items():
        cx,cy,w,h=LAYOUT[name]
        fill,stroke,ink=COLORS[classes[name]]
        if diamond:
            draw.polygon([(cx,cy-h/2),(cx+w/2,cy),(cx,cy+h/2),(cx-w/2,cy)],fill=fill,outline=stroke,width=3)
            centered(text,cx,cy,size=27,color=ink,width=w*.65,height=h*.62)
        else:
            draw.rounded_rectangle((cx-w/2,cy-h/2,cx+w/2,cy+h/2),radius=17,fill=fill,outline=stroke,width=3)
            centered(text,cx,cy,size=27 if name!='reward_action' else 25,color=ink,width=w-38,height=h-25)
    for edge,label in edges.items():
        if label is not None:
            x,y=LABEL_POSITIONS[edge]
            text=label.replace('；','\n')
            f=font(22);b=draw.multiline_textbbox((0,0),text,font=f,spacing=5,align='center')
            tw,th=b[2]-b[0],b[3]-b[1]
            draw.rounded_rectangle((x-tw/2-7,y-th/2-5,x+tw/2+7,y+th/2+5),radius=5,fill='#ffffff')
            centered(text,x,y,size=22)
    centered('未决任务再分两类',1640,970,size=25,color='#713f12')
    draw.text((1370,1380),'读图要点',font=font(27),fill='#12233f')
    for yy,color,label in [(1430,'#ffedd5','橙色：专门认证'),(1472,'#dbeafe','蓝色：收益评分 + 预算筛选'),(1514,'#dcfce7','绿色：共同观测与分类报告')]:
        draw.rounded_rectangle((1372,yy+5,1396,yy+29),radius=5,fill=color,outline='#9ba5b2',width=1)
        draw.text((1412,yy),label,font=font(22),fill='#253247')
    draw.rounded_rectangle((1365,1585,1915,1748),radius=13,fill='#f8f9fb',outline='#d5dce5',width=2)
    centered('异常约定：区间交集为空时\n永久全未决，关闭专门认证；\n收益采样和真实统计更新继续。',1640,1667,size=22,width=520,height=145,color='#4b5563')
    draw.text((68,1815),'负标签不删除臂；暂缓的臂仍报告未决；新臂到来后重新计算任务和标签。',font=font(24),fill='#566172')

    png=ROOT/'fccp_flowchart.png';pdf=ROOT/'fccp_flowchart.pdf'
    img.save(png,dpi=(180,180))
    img.save(pdf,'PDF',resolution=180.)
    record={'passed':True,'canonical_source':'fccp_flowchart.md','nodes':len(nodes),'edges':len(edges),'rendered_edges_match_canonical_mermaid':True,'size_pixels':list(img.size),'font':str(font_path),'sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'fccp_flowchart.md',Path(__file__)]},'outputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [png,pdf]}}
    (ROOT/'render-validation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(record,ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--font',type=Path,default=Path('C:/Windows/Fonts/msyh.ttc'))
    args=parser.parse_args()
    if not args.font.is_file():
        raise FileNotFoundError('Use --font with a CJK-capable .ttf/.ttc font path.')
    render(args.font)
