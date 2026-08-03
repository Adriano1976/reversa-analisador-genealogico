// Reversa Docs - dados embedados do mini-site (gerado pelo Publisher)
// Fontes intermediarias: assets/data/*.json (mantidos para regeneracao granular)
window.RV_DATA = {
  modules: {
  "schemaVersion": 1,
  "generatedAt": "2026-08-03T14:05:00Z",
  "project": "analisador-genealogico",
  "language": "Python/Flask",
  "modules": [
    {
      "id": "app",
      "name": "app.py (monolito)",
      "path": "analisador-genealogico/app.py",
      "type": "entrypoint",
      "language": "python",
      "folder": "analisador-genealogico",
      "loc": 887,
      "complexity": 9,
      "description": "Aplicação Web Flask monolítica com rotas, parsing e renderização acopladas."
    },
    {
      "id": "config-setup",
      "name": "Configuração e setup",
      "path": "analisador-genealogico/app.py",
      "type": "config",
      "language": "python",
      "folder": "analisador-genealogico",
      "loc": 37,
      "complexity": 1,
      "description": "Criação da app Flask, secret_key, pastas uploads/static e tabela de faixas cM (SHARED_CM_DATA)."
    },
    {
      "id": "gedcom-parsing",
      "name": "Parsing GEDCOM",
      "path": "analisador-genealogico/app.py",
      "type": "parser",
      "language": "python",
      "folder": "analisador-genealogico",
      "loc": 33,
      "complexity": 4,
      "description": "load_gedcom_and_build_graph e build_graph_from_parser: leitura de INDI/FAM e construção do grafo networkx."
    },
    {
      "id": "dna-aggregation",
      "name": "Agregação de DNA",
      "path": "analisador-genealogico/app.py",
      "type": "processor",
      "language": "python",
      "folder": "analisador-genealogico",
      "loc": 35,
      "complexity": 6,
      "description": "Leitura tolerante do CSV de matches, detecção de colunas, groupby por _group_key e soma de cM."
    },
    {
      "id": "name-matching",
      "name": "Matching difuso de nomes",
      "path": "analisador-genealogico/app.py",
      "type": "algorithm",
      "language": "python",
      "folder": "analisador-genealogico",
      "loc": 132,
      "complexity": 8,
      "description": "Normalização, mojibake, indexação e scoring thefuzz com regras anti-falso-positivo (HARD_MIN/GIVEN_MIN)."
    },
    {
      "id": "path-finder",
      "name": "Busca de caminho genealógico",
      "path": "analisador-genealogico/app.py",
      "type": "algorithm",
      "language": "python",
      "folder": "analisador-genealogico",
      "loc": 27,
      "complexity": 7,
      "description": "find_ancestral_path (BFS bidirecional) e find_indirect_path (shortest_path networkx via afinidade)."
    },
    {
      "id": "mermaid-render",
      "name": "Renderização Mermaid",
      "path": "analisador-genealogico/app.py",
      "type": "presenter",
      "language": "python",
      "folder": "analisador-genealogico",
      "loc": 176,
      "complexity": 8,
      "description": "generate_mermaid_graph e bridge indireto: geração de diagramas flowch de ancestralidade."
    },
    {
      "id": "routes",
      "name": "Rotas HTTP",
      "path": "analisador-genealogico/app.py",
      "type": "web",
      "language": "python",
      "folder": "analisador-genealogico",
      "loc": 90,
      "complexity": 6,
      "description": "Rota / (GET/POST) orquestrando upload_gedcom, dna_analysis e path_search."
    },
    {
      "id": "templates-index",
      "name": "Template index.html",
      "path": "analisador-genealogico/templates/index.html",
      "type": "frontend",
      "language": "html",
      "folder": "analisador-genealogico",
      "loc": 334,
      "complexity": 5,
      "description": "View Jinja2 + Bootstrap 5 com formulários e renderização de resultados."
    },
    {
      "id": "static-graph",
      "name": "graph_path_search.html",
      "path": "analisador-genealogico/static/graph_path_search.html",
      "type": "frontend",
      "language": "html",
      "folder": "analisador-genealogico",
      "loc": 480,
      "complexity": 5,
      "description": "Visualização interativa do grafo de busca de caminho."
    }
  ]
},
  deps: {
  "schemaVersion": 1,
  "generatedAt": "2026-08-03T14:05:00Z",
  "project": "analisador-genealogico",
  "language": "Python/Flask",
  "nodes": [
    "app", "config-setup", "gedcom-parsing", "dna-aggregation",
    "name-matching", "path-finder", "mermaid-render", "routes",
    "templates-index", "static-graph"
  ],
  "edges": [
    {"source": "app", "target": "config-setup"},
    {"source": "app", "target": "routes"},
    {"source": "routes", "target": "gedcom-parsing"},
    {"source": "routes", "target": "dna-aggregation"},
    {"source": "routes", "target": "name-matching"},
    {"source": "routes", "target": "path-finder"},
    {"source": "name-matching", "target": "gedcom-parsing"},
    {"source": "path-finder", "target": "gedcom-parsing"},
    {"source": "routes", "target": "mermaid-render"},
    {"source": "routes", "target": "templates-index"},
    {"source": "routes", "target": "static-graph"},
    {"source": "mermaid-render", "target": "path-finder"},
    {"source": "mermaid-render", "target": "name-matching"}
  ],
  "cycles": []
},
  metrics: {
  "schemaVersion": 1,
  "generatedAt": "2026-08-03T14:15:00Z",
  "project": "analisador-genealogico",
  "treemap_loc_by_folder": [
    {"folder": "analisador-genealogico (app.py)", "loc": 887, "modules": 8},
    {"folder": "analisador-genealogico/templates", "loc": 334, "modules": 1},
    {"folder": "analisador-genealogico/static", "loc": 480, "modules": 1}
  ],
  "top_complexity": [
    {"id": "app.py (monolito)", "complexity": 9, "loc": 887},
    {"id": "name-matching", "complexity": 8, "loc": 132},
    {"id": "mermaid-render", "complexity": 8, "loc": 176},
    {"id": "path-finder", "complexity": 7, "loc": 27},
    {"id": "routes", "complexity": 6, "loc": 90},
    {"id": "dna-aggregation", "complexity": 6, "loc": 35},
    {"id": "templates-index", "complexity": 5, "loc": 334},
    {"id": "static-graph", "complexity": 5, "loc": 480},
    {"id": "gedcom-parsing", "complexity": 4, "loc": 33},
    {"id": "config-setup", "complexity": 1, "loc": 37}
  ],
  "loc_histogram": {
    "bins": [0, 50, 100, 200, 500, 1000],
    "counts": [5, 1, 2, 1, 1, 0]
  },
  "dependency_sankey": {
    "nodes": [
      {"id": "app.py (monolito)"},
      {"id": "routes"},
      {"id": "gedcom-parsing"},
      {"id": "dna-aggregation"},
      {"id": "name-matching"},
      {"id": "path-finder"},
      {"id": "mermaid-render"},
      {"id": "templates/static"}
    ],
    "links": [
      {"source": "app.py (monolito)", "target": "routes", "value": 1},
      {"source": "routes", "target": "gedcom-parsing", "value": 2},
      {"source": "routes", "target": "dna-aggregation", "value": 2},
      {"source": "routes", "target": "name-matching", "value": 3},
      {"source": "routes", "target": "path-finder", "value": 3},
      {"source": "routes", "target": "mermaid-render", "value": 3},
      {"source": "routes", "target": "templates/static", "value": 4}
    ]
  },
  "language_distribution": [
    {"language": "Python", "modules": 8, "loc": 887},
    {"language": "HTML", "modules": 2, "loc": 814}
  ]
},
  featuresIndex: {
  "schemaVersion": 1,
  "generatedAt": "2026-08-03T14:20:00Z",
  "project": "analisador-genealogico",
  "specs": [
    {
      "id": "upload-gedcom",
      "slug": "upload-gedcom",
      "title": "Upload e Parsing de GEDCOM",
      "summary": "Recebe um arquivo GEDCOM (.ged), faz o parsing da árvore genealógica via ged4py e constrói o grafo NetworkX de pessoas e famílias.",
      "hasRequirements": true
    },
    {
      "id": "busca-caminho",
      "slug": "busca-caminho",
      "title": "Busca de Caminho (Path Search)",
      "summary": "Busca a conexão genealógica entre duas pessoas: direta por ancestral comum (BFS bidirecional) ou indireta por afinidade via BFS no grafo.",
      "hasRequirements": true
    },
    {
      "id": "analise-dna",
      "slug": "analise-dna",
      "title": "Análise de DNA (DNA Analysis)",
      "summary": "Cruza a árvore GEDCOM com um CSV de matches de DNA: agrega cM, faz matching difuso de nomes, prevê parentesco e ordena por cM.",
      "hasRequirements": true
    }
  ]
},
  timeline: {},
  glossary: {},
  sealSvg: "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"800\" height=\"800\" viewBox=\"0 0 800 800\">\n  <defs>\n    <radialGradient id=\"bg\" cx=\"50%\" cy=\"45%\" r=\"70%\">\n      <stop offset=\"0%\" stop-color=\"#23262c\"/>\n      <stop offset=\"100%\" stop-color=\"#181a1e\"/>\n    </radialGradient>\n    <linearGradient id=\"gem\" x1=\"0%\" y1=\"0%\" x2=\"100%\" y2=\"100%\">\n      <stop offset=\"0%\" stop-color=\"#4f8cff\"/>\n      <stop offset=\"100%\" stop-color=\"#2f5cb0\"/>\n    </linearGradient>\n    <filter id=\"glow\" x=\"-40%\" y=\"-40%\" width=\"180%\" height=\"180%\">\n      <feGaussianBlur stdDeviation=\"14\" result=\"b\"/>\n      <feMerge><feMergeNode in=\"b\"/><feMergeNode in=\"SourceGraphic\"/></feMerge>\n    </filter>\n  </defs>\n  <rect width=\"800\" height=\"800\" fill=\"url(#bg)\"/>\n  <g stroke=\"#3a3d45\" stroke-width=\"2\" fill=\"none\">\n    <circle cx=\"400\" cy=\"400\" r=\"330\"/>\n    <circle cx=\"400\" cy=\"400\" r=\"262\"/>\n    <circle cx=\"400\" cy=\"400\" r=\"190\"/>\n    <circle cx=\"400\" cy=\"400\" r=\"120\"/>\n  </g>\n  <g stroke=\"#4f8cff\" stroke-opacity=\"0.25\" stroke-width=\"1.5\">\n    <line x1=\"400\" y1=\"70\" x2=\"400\" y2=\"730\"/>\n    <line x1=\"70\" y1=\"400\" x2=\"730\" y2=\"400\"/>\n    <line x1=\"166\" y1=\"166\" x2=\"634\" y2=\"634\"/>\n    <line x1=\"166\" y1=\"634\" x2=\"634\" y2=\"166\"/>\n    <line x1=\"215\" y1=\"110\" x2=\"585\" y2=\"690\"/>\n    <line x1=\"110\" y1=\"215\" x2=\"690\" y2=\"585\"/>\n    <line x1=\"585\" y1=\"110\" x2=\"215\" y2=\"690\"/>\n    <line x1=\"110\" y1=\"585\" x2=\"690\" y2=\"215\"/>\n  </g>\n  <g fill=\"#4f8cff\" filter=\"url(#glow)\">\n    <polygon points=\"400,238 520,400 400,562 280,400\"/>\n    <polygon points=\"400,320 446,400 400,480 354,400\" fill=\"#d18a5a\" opacity=\"0.9\"/>\n  </g>\n  <g fill=\"#d18a5a\">\n    <circle cx=\"400\" cy=\"238\" r=\"12\"/>\n    <circle cx=\"520\" cy=\"400\" r=\"12\"/>\n    <circle cx=\"400\" cy=\"562\" r=\"12\"/>\n    <circle cx=\"280\" cy=\"400\" r=\"12\"/>\n  </g>\n  <g fill=\"#6b7d99\">\n    <circle cx=\"400\" cy=\"110\" r=\"6\"/>\n    <circle cx=\"690\" cy=\"400\" r=\"6\"/>\n    <circle cx=\"400\" cy=\"690\" r=\"6\"/>\n    <circle cx=\"110\" cy=\"400\" r=\"6\"/>\n    <circle cx=\"400\" cy=\"70\" r=\"4\"/>\n    <circle cx=\"730\" cy=\"400\" r=\"4\"/>\n    <circle cx=\"400\" cy=\"730\" r=\"4\"/>\n    <circle cx=\"70\" cy=\"400\" r=\"4\"/>\n  </g>\n  <g fill=\"#8b909a\" font-family=\"Consolas, monospace\" font-size=\"22\" text-anchor=\"middle\">\n    <text x=\"400\" y=\"360\" fill=\"#d18a5a\">G</text>\n  </g>\n</svg>",
  sealMiniSvg: "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"64\" height=\"64\" viewBox=\"0 0 64 64\">\n  <rect width=\"64\" height=\"64\" rx=\"12\" fill=\"#23262c\"/>\n  <g stroke=\"#3a3d45\" stroke-width=\"1\" fill=\"none\">\n    <circle cx=\"32\" cy=\"32\" r=\"27\"/>\n    <circle cx=\"32\" cy=\"32\" r=\"20\"/>\n    <circle cx=\"32\" cy=\"32\" r=\"13\"/>\n  </g>\n  <g stroke=\"#4f8cff\" stroke-opacity=\"0.3\" stroke-width=\"1\">\n    <line x1=\"32\" y1=\"4\" x2=\"32\" y2=\"60\"/>\n    <line x1=\"4\" y1=\"32\" x2=\"60\" y2=\"32\"/>\n    <line x1=\"12\" y1=\"12\" x2=\"52\" y2=\"52\"/>\n    <line x1=\"12\" y1=\"52\" x2=\"52\" y2=\"12\"/>\n  </g>\n  <polygon points=\"32,16 46,32 32,48 18,32\" fill=\"#4f8cff\"/>\n  <polygon points=\"32,24 40,32 32,40 24,32\" fill=\"#d18a5a\" opacity=\"0.9\"/>\n  <g fill=\"#6b7d99\">\n    <circle cx=\"32\" cy=\"5.5\" r=\"1.6\"/>\n    <circle cx=\"58.5\" cy=\"32\" r=\"1.6\"/>\n    <circle cx=\"32\" cy=\"58.5\" r=\"1.6\"/>\n    <circle cx=\"5.5\" cy=\"32\" r=\"1.6\"/>\n  </g>\n</svg>",
  seedShort: "b1467bf8",
  nav: [
    {"id": "index", "href": "index.html", "label": "Visão geral"},
    {"id": "arquitetura", "href": "arquitetura.html", "label": "Arquitetura 3D"},
    {"id": "modulos", "href": "modulos.html", "label": "Módulos"},
    {"id": "metricas", "href": "metricas.html", "label": "Métricas"},
    {"id": "deck", "href": "deck.html", "label": "Deck"},
    {"id": "features", "href": "features/upload-gedcom.html", "label": "Features"}
  ],
  config: {
    "visualStyle": "sober",
    "readerProfile": "stakeholder",
    "depth": "full"
  }
};