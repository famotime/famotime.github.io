// script.js
(async function(){
    const resp = await fetch('data.json');
    const raw = await resp.json();
    // 1. 数据清洗 & 增强
    const data = raw.map(d => ({
      ...d,
      createTime: new Date(d.createTime),
      yearMonth: d.createTime.slice(0,7), // "YYYY-MM"
    }));

    // 工具：分组
    function groupBy(arr, keyFn) {
      return arr.reduce((acc,cur)=>{
        const k = keyFn(cur);
        (acc[k]||(acc[k]=[])).push(cur);
        return acc;
      }, {});
    }

    // ----------------------------------------------------------------
    // 1. 时间趋势
    // 1.1 每月发文量
    const byMonth = groupBy(data, d=>d.yearMonth);
    const months = Object.keys(byMonth).sort();
    const postCounts = months.map(m=>byMonth[m].length);
    Plotly.newPlot('monthlyPostsChart', [{
      x: months,
      y: postCounts,
      type: 'bar',
      marker: {color:'#3498db'}
    }], {
      title: '每月发文量',
      xaxis:{title:'年月'},
      yaxis:{title:'发文数'}
    });

    // 1.2 各指标累积趋势
    const metrics = ['readCount','likeCount','commentCount','shareCount'];
    const cumul = metrics.map(m=>{
      let cum=0;
      const y = months.map(mo=>{
        const sum = byMonth[mo].reduce((s,d)=>s+d[m],0);
        cum += sum;
        return cum;
      });
      return { x:months, y, name:m, mode:'lines' };
    });
    Plotly.newPlot('cumulativeMetricsChart', cumul, {
      title:'各项指标累积趋势（按月）',
      xaxis:{title:'时间'},
      yaxis:{title:'累计次数'}
    });

    // ----------------------------------------------------------------
    // 2. 分布 & Top10
    function drawDist(metric, chartId, tableId){
      const vals = data.map(d=>d[metric]);
      Plotly.newPlot(chartId, [{
        x: vals,
        type: 'histogram',
        nbinsx: 30,
        marker:{color:'#9b59b6'}
      }], {
        title: metric + ' 分布'
      });

      // Top10
      const top10 = data.slice()
        .sort((a,b)=>b[metric]-a[metric])
        .slice(0,10);
      let html = '<table><thead><tr>'
        +'<th>ID</th><th>标题</th><th>'+metric+'</th></tr></thead><tbody>';
      top10.forEach(d=>{
        html += `<tr><td>${d.id}</td><td>${d.title}</td><td>${d[metric]}</td></tr>`;
      });
      html += '</tbody></table>';
      document.getElementById(tableId).innerHTML = html;
    }
    drawDist('readCount','readDist','readTop10');
    drawDist('likeCount','likeDist','likeTop10');
    drawDist('commentCount','commentDist','commentTop10');
    drawDist('shareCount','shareDist','shareTop10');

    // ----------------------------------------------------------------
    // 3. 相关性矩阵
    function pearson(x,y){
      const n=x.length;
      const mx = x.reduce((a,b)=>a+b,0)/n;
      const my = y.reduce((a,b)=>a+b,0)/n;
      let num=0,dx2=0,dy2=0;
      for(let i=0;i<n;i++){
        const dx = x[i]-mx, dy = y[i]-my;
        num += dx*dy; dx2 += dx*dx; dy2 += dy*dy;
      }
      return num/Math.sqrt(dx2*dy2);
    }
    // 构建矩阵
    const corr = metrics.map(mi=>{
      return metrics.map(mj=>{
        const xi = data.map(d=>d[mi]);
        const yj = data.map(d=>d[mj]);
        return pearson(xi,yj);
      });
    });
    Plotly.newPlot('corrMatrix', [{
      z: corr,
      x: metrics,
      y: metrics,
      type: 'heatmap',
      colorscale:'RdBu',
      zmin:-1, zmax:1
    }], {
      title:'阅读/点赞/评论/分享 相关系数矩阵'
    });

    // ----------------------------------------------------------------
    // 4. 引用关系网络
    // 4.1 节点与边
    const nodes = [];
    const edges = [];
    data.forEach(d=>{
      nodes.push({
        id: d.id,
        label: d.id,
        title: d.title,
        value: d.id_links.length+1
      });
      d.id_links.forEach(t=>{
        edges.push({ from: d.id, to: t });
      });
    });
    const container = document.getElementById('networkVis');
    const network = new vis.Network(container, { nodes, edges }, {
      nodes:{shape:'dot',scaling:{min:5,max:30}},
      edges:{arrows:'to'},
      physics:{stabilization:false}
    });

    // 4.2 网络度量：入度/出度 Top10
    const inDeg={}, outDeg={};
    edges.forEach(e=>{
      outDeg[e.from] = (outDeg[e.from]||0)+1;
      inDeg[e.to]   = (inDeg[e.to]||0)+1;
    });
    function topN(obj,n){
      return Object.entries(obj)
        .sort((a,b)=>b[1]-a[1])
        .slice(0,n);
    }
    const topIn = topN(inDeg,10);
    const topOut= topN(outDeg,10);
    let mhtml = '<h3>网络度量 Top10</h3>';
    mhtml += '<p>▶ 入度最高 Top10: '+ topIn.map(r=>`${r[0]}(${r[1]})`).join(', ') +'</p>';
    mhtml += '<p>▶ 出度最高 Top10: '+ topOut.map(r=>`${r[0]}(${r[1]})`).join(', ') +'</p>';
    document.getElementById('networkMetrics').innerHTML = mhtml;

  })();
