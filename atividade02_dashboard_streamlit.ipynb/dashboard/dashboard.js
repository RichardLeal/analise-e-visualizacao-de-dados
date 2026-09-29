/* Streamlit component protocol, with viewport-sized charts and accessible native controls. */
const $ = id => document.getElementById(id);
const numberBR = new Intl.NumberFormat('pt-BR', {maximumFractionDigits: 2});
const shortMetrics = {valor_m2:'Valor/m² mediano',base_de_calculo:'Base de cálculo mediana',registros:'Número de registros',compatibilidade:'Compatibilidade histórica',variacao:'Variação do valor/m²'};
let payload, state, pickerKey, pickerValues = [], resizeTimer, barView, renderVersion=0;
function send(type, extra={}) { window.parent.postMessage({isStreamlitMessage:true,type,...extra}, '*'); }
function fitFrame(){
  let height;
  try { height = window.parent.innerHeight - 2; } catch { height = window.innerHeight; }
  send('streamlit:setFrameHeight', {height});
}
function update(patch){
  state = {...state,...patch};
  $('loading').hidden=false;
  send('streamlit:setComponentValue',{value:{state, nonce:Date.now()},dataType:'json'});
}
function selectOptions(element, options, selected, label=x=>x){
  element.replaceChildren(...options.map(value=>{const o=document.createElement('option');o.value=value;o.textContent=label(value);return o;}));
  element.value=selected || '';
}
function addRange(key, label, unit, step){
  const [min,max]=payload.defaults[key];
  const root=document.createElement('div');root.className='range-group';
  const heading=document.createElement('label');heading.className='range-label';heading.textContent=label;root.append(heading);
  const track=document.createElement('div');track.className='range-track';
  const values=document.createElement('div');values.className='range-values';
  const sliders=[], numbers=[];
  for(let i=0;i<2;i++){
    const slider=document.createElement('input');slider.type='range';slider.min=min;slider.max=max;slider.step=step;slider.value=state[key][i];slider.setAttribute('aria-label',`${label}: ${i?'máximo':'mínimo'}`);
    const numeric=document.createElement('input');numeric.type='text';numeric.inputMode='decimal';numeric.value=key==='years'||key==='construction'?String(state[key][i]):numberBR.format(state[key][i]);numeric.title=`${label} (${unit})`;numeric.setAttribute('aria-label',`${label}: ${i?'limite superior':'limite inferior'}`);
    numeric.disabled=slider.disabled=key==='construction'&&!state.construction_active;
    sliders.push(slider);numbers.push(numeric);track.append(slider);values.append(numeric);
    if(i===0){const separator=document.createElement('span');separator.textContent='–';values.append(separator);}
    const parse = text => Number(text.replaceAll('.','').replace(',','.'));
    const display = value => key==='years'||key==='construction'?String(value):numberBR.format(value);
    function clamp(v){const other=parse(numbers[1-i].value);return i?Math.max(other,Math.min(max,v)):Math.min(other,Math.max(min,v));}
    slider.oninput=()=>{const v=clamp(Number(slider.value));numeric.value=display(v);slider.value=v;};
    slider.onchange=()=>{const range=[...state[key]];range[i]=parse(numeric.value);update({[key]:range});};
    numeric.onchange=()=>{const parsed=parse(numeric.value);if(!Number.isFinite(parsed)){numeric.value=display(state[key][i]);return;}const v=clamp(parsed);numeric.value=display(v);slider.value=v;const range=[...state[key]];range[i]=v;update({[key]:range});};
  }
  root.append(track,values);$('ranges').append(root);
}
function openPicker(key){
  pickerKey=key;pickerValues=[...state[key]];
  $('picker-title').textContent=key==='comparison'?'Comparar até quatro bairros':'Selecionar bairros';
  $('picker-search').value='';drawPicker();$('picker').showModal();$('picker-search').focus();
}
function drawPicker(){
  const query=$('picker-search').value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  $('picker-count').textContent=pickerKey==='comparison'?`${pickerValues.length} de 4 selecionados. Sem seleção: bairro em foco.`:`${pickerValues.length} selecionados. Sem seleção: todos os bairros.`;
  const options=pickerKey==='comparison'?payload.options:payload.names;
  $('picker-options').replaceChildren(...options.filter(n=>n.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().includes(query)).map(name=>{
    const label=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.checked=pickerValues.includes(name);
    check.disabled=pickerKey==='comparison'&&!check.checked&&pickerValues.length>=4;
    check.onchange=()=>{pickerValues=check.checked?[...pickerValues,name]:pickerValues.filter(n=>n!==name);drawPicker();};label.append(check,document.createTextNode(name));return label;
  }));
}
const help={
  map:['Mapa e recorte','P3 · Como o valor por metro quadrado varia entre bairros? O mapa mantém todos os polígonos oficiais. Cinza identifica dados ausentes ou insuficientes para a métrica. Compatibilidade = registros que atendem ao perfil ÷ registros do bairro no período, antes dos filtros de valor, área e construção. Variação usa os dois anos extremos e exige o mínimo em ambos.'],
  line:['Evolução temporal','P1 · Como o valor mediano dos apartamentos evoluiu entre 2020 e 2025? A referência de Porto Alegre usa os mesmos filtros de período e perfil, com todos os bairros. Mostramos o bairro em foco e até três outros comparados, limitando a quatro bairros. Pontos com amostra abaixo do mínimo ficam ausentes; não há interpolação. Valores nominais, sem correção da inflação.'],
  scatter:['Posicionamento dos bairros','Cada ponto é um bairro: valor/m² mediano no eixo horizontal e quantidade de registros no vertical. O bairro em foco aparece destacado. Quantidade não mede liquidez, estoque disponível nem tempo de venda.'],
  comparison:['Comparação entre bairros','P2 · As barras ordenam as medianas por bairro, respeitando o mínimo de registros. O número exibido se adapta à altura e é informado abaixo do gráfico; alterne Maiores/Menores para investigar os dois extremos. A tabela compara até quatro bairros. — indica medida indisponível ou amostra insuficiente. A variação exige o mínimo nos dois anos extremos. Ano de construção mediano usa somente valores informados.'],
};
function showHelp(key){$('info-title').textContent=help[key][0];$('info-content').textContent=help[key][1];$('info').showModal();}
function showAbout(){
  $('info-title').textContent='Sobre os dados e a metodologia';
  $('info-content').innerHTML=`<p><strong>Fonte:</strong> <a href="https://dadosabertos.poa.br/dataset/itbi" target="_blank" rel="noopener">ITBI da Prefeitura de Porto Alegre</a>, 2020–2025. Licença CC-BY conforme documentação do projeto. Limites oficiais SMURB/PMPA, LC 12.112/2016.</p><p><strong>Preparação preservada:</strong> remoção de duplicatas, reconstrução de guias, apartamentos de unidade única, base e área positivas, exclusão de bairro vazio e zona indefinida, corte P1–P99 de valor/m².</p><p><strong>Mediana:</strong> valor central da distribuição. Valor/m² = base fiscal do ITBI ÷ área privativa. A base de cálculo não equivale necessariamente ao preço de mercado.</p><p><strong>Filtros:</strong> contexto = período e bairros; perfil = valor, área e construção. Compatibilidade divide os compatíveis pelo contexto anterior aos filtros de perfil. O mínimo se aplica ao denominador nesse modo, à amostra filtrada nas medianas e aos dois extremos na variação.</p><p><strong>Limitações:</strong> valores nominais, mudanças de composição, transmissões parciais mantidas, anos de construção ausentes e corte dos extremos. JAR ITU SABARA permanece nas tabelas e séries sem atribuição artificial a um polígono. O ano é o ano da base.</p><p><strong>Referência da cidade:</strong> mesmos filtros de período e perfil, abrangendo todos os bairros. Contagens são de registros, não de imóveis únicos, oferta atual ou liquidez.</p><p><strong>Imagem:</strong> o brasão municipal é o recurso real disponível. Não há fotografias de bairros no projeto.</p>`;
  $('info').showModal();
}
function renderControls(){
  $('ranges').replaceChildren();
  addRange('years','Período · ano da base','ano',1);
  addRange('value','Base de cálculo (R$)','R$',.01);
  addRange('area','Área privativa (m²)','m²',.01);
  addRange('construction','Ano de construção','ano',1);
  $('construction-active').checked=state.construction_active;$('include-missing').checked=state.include_missing;
  $('include-missing').disabled=!state.construction_active;
  $('include-missing').parentElement.title=`${payload.missing_construction} registros sem ano de construção`;
  $('minimum').value=state.minimum;
  $('neighborhoods').textContent=state.neighborhoods.length?`${state.neighborhoods.length} bairros selecionados ▾`:'Todos os bairros ▾';
  $('comparison').textContent=state.comparison.length?`${state.comparison.length} selecionados ▾`:'Selecionar até 4 ▾';
  selectOptions($('focus'),payload.options,state.focus);
  selectOptions($('line-metric'),['base_de_calculo','valor_m2'],state.line_metric,k=>shortMetrics[k]);
  selectOptions($('bar-metric'),['base_de_calculo','valor_m2'],state.bar_metric,k=>k==='base_de_calculo'?'Base de cálculo':'Valor/m²');
  $('order').value=state.ascending?'asc':'desc';
  $('map-metrics').replaceChildren(...Object.keys(payload.metrics).map(key=>{
    const label=document.createElement('label'),input=document.createElement('input');input.type='radio';input.name='map-metric';input.value=key;input.checked=key===state.metric;input.onchange=()=>update({metric:key});label.append(input,document.createTextNode(shortMetrics[key]));return label;
  }));
}
function renderTable(){
  const table=$('comparison-table');table.replaceChildren();
  const head=document.createElement('thead'),tr=document.createElement('tr');
  for(const name of ['Indicador',...payload.compared]){const th=document.createElement('th');th.textContent=name;th.scope='col';tr.append(th);}head.append(tr);table.append(head);
  const body=document.createElement('tbody');
  for(const row of payload.table){const tr=document.createElement('tr');const label=document.createElement('th');label.scope='row';label.textContent=row.label;tr.append(label);for(const value of row.values){const td=document.createElement('td');td.textContent=value;tr.append(td);}body.append(tr);}table.append(body);
}
async function renderCharts(){
  if(!payload || !window.Plotly || !window.vegaEmbed) return;
  const version=++renderVersion;
  for(const key of ['line','scatter']){
    const container=$(key), rect=container.getBoundingClientRect(), fig=payload[key];
    const compact=window.innerHeight<850;
    const layout={...fig.layout,width:Math.floor(rect.width),height:Math.floor(rect.height),autosize:false,
      margin:{l:66,r:16,t:key==='line'?48:16,b:42},
      font:{...fig.layout.font,size:11}};
    layout.xaxis={...layout.xaxis,title:{text:key==='line'?'Ano':'Valor/m² mediano (R$/m²)',font:{size:10}},nticks:compact?4:6};
    layout.yaxis={...layout.yaxis,title:{text:key==='scatter'?'Registros':state.line_metric==='valor_m2'?'R$/m²':'R$',font:{size:12}},nticks:Math.max(5,Math.floor(rect.height/48)),tickfont:{size:11}};
    layout.yaxis.tickformat=',.0f';
    if(key==='scatter')layout.xaxis.tickformat=',.0f';
    await Plotly.react(container,fig.data,layout,{responsive:false,displayModeBar:false,locale:'pt-BR'});
  }
  if(version!==renderVersion)return;
  const rect=$('bars').getBoundingClientRect();
  const count=Math.min(8,Math.max(1,Math.floor((rect.height-23)/19)),payload.eligible_count);
  const spec=structuredClone(payload.bars);
  const values=spec.data.values || spec.datasets?.[spec.data.name] || [];
  const ordered=[...values].sort((a,b)=>state.ascending?a[state.bar_metric]-b[state.bar_metric]:b[state.bar_metric]-a[state.bar_metric]).slice(0,count);
  spec.data={values:ordered};delete spec.datasets;
  spec.width=Math.max(80,Math.floor(rect.width)-145);spec.height=Math.max(30,Math.floor(rect.height)-24);
  spec.padding={left:0,right:4,top:0,bottom:0};spec.config={...spec.config,font:'Arial',axis:{labelFontSize:10,titleFontSize:10,gridColor:'#edf1f5'}};
  spec.encoding.x.axis={tickCount:3,title:null,labelExpr:"datum.value >= 1000000 ? replace(format(datum.value/1000000, '.1f'), '.', ',') + ' mi' : datum.value >= 1000 ? replace(format(datum.value/1000, '.0f'), '.', ',') + ' mil' : datum.value"};spec.encoding.y.axis={labelLimit:125,labelFontSize:10};
  if(barView)barView.finalize();
  const result=await vegaEmbed($('bars'),spec,{actions:false,renderer:'svg'});barView=result.view;
  $('bar-limit').textContent=`${count} de ${payload.eligible_count} bairros com ≥ ${state.minimum} registros · ${state.ascending?'menores':'maiores'} medianas`;
}
async function render(args){
  payload=args.payload;state=structuredClone(payload.state);$('loading').hidden=true;$('error').hidden=true;
  $('crest').src=$('focus-crest').src=args.crest;
  $('total').textContent=payload.total;
  $('context-note').textContent=payload.note;
  $('map-title').textContent=shortMetrics[state.metric]+' por bairro';
  $('map-note').textContent=payload.metric_note;
  $('map').srcdoc=payload.map_html;
  $('empty').hidden=!payload.empty;
  renderControls();renderTable();
  $('kpis').replaceChildren(...payload.kpis.map(k=>{
    const box=document.createElement('div');box.className='kpi';
    for(const [tag,cls,text] of [['strong','',k.value],['span','label',k.label],['span','delta'+(k.positive?' positive':''),(k.positive?'↑ +':'')+k.delta],['span','reference',k.share?'dos registros da cidade':'vs. Porto Alegre']]){const e=document.createElement(tag);e.className=cls;e.textContent=text;box.append(e);}return box;
  }));
  $('focus-note').textContent=payload.focus_sufficient?'Mesmo período e perfil da cidade · contorno azul no mapa.':`Amostra insuficiente para medianas (mínimo ${state.minimum}).`;
  if(state.focus==='JAR ITU SABARA')$('focus-note').textContent+=' Sem polígono oficial.';
  fitFrame();requestAnimationFrame(()=>renderCharts().catch(showError));
}
function showError(error){$('error').textContent='Não foi possível renderizar o painel: '+error.message;$('error').hidden=false;console.error(error);}
window.addEventListener('message',event=>{if(event.source===window.parent && event.data.type==='streamlit:render')render(event.data.args).catch(showError);});
window.addEventListener('resize',()=>{fitFrame();clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>renderCharts().catch(showError),150);});
new ResizeObserver(()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>renderCharts().catch(showError),150);}).observe(document.querySelector('.panels'));
$('construction-active').onchange=e=>update({construction_active:e.target.checked});
$('include-missing').onchange=e=>update({include_missing:e.target.checked});
$('minimum').onchange=e=>update({minimum:Math.max(1,Math.min(116199,Number(e.target.value)||1))});
$('focus').onchange=e=>update({focus:e.target.value});
$('line-metric').onchange=e=>update({line_metric:e.target.value});
$('bar-metric').onchange=e=>update({bar_metric:e.target.value});
$('order').onchange=e=>update({ascending:e.target.value==='asc'});
$('reset').onclick=()=>update(payload.defaults);
$('neighborhoods').onclick=()=>openPicker('neighborhoods');$('comparison').onclick=()=>openPicker('comparison');
$('picker-search').oninput=drawPicker;
$('picker-close').onclick=()=>$('picker').close();$('picker-clear').onclick=()=>{pickerValues=[];drawPicker();};
$('picker-apply').onclick=()=>{$('picker').close();update({[pickerKey]:pickerValues});};
$('info-close').onclick=()=>$('info').close();$('about-button').onclick=showAbout;
document.querySelectorAll('[data-help]').forEach(b=>b.onclick=()=>showHelp(b.dataset.help));
document.querySelectorAll('[data-panel]').forEach(b=>b.onclick=()=>{document.querySelectorAll('nav button').forEach(x=>x.classList.remove('active'));b.classList.add('active');const panel=$(b.dataset.panel);panel.focus({preventScroll:true});panel.classList.add('flash');setTimeout(()=>panel.classList.remove('flash'),1200);});
send('streamlit:componentReady',{apiVersion:1});fitFrame();
