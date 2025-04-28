// API para listar aplicativos disponíveis
module.exports = (req, res) => {
  // Lista de aplicativos disponíveis (sem extensão .exe)
  const appsList = [
    {
      id: 'neuraai-assistant',
      title: 'neuraai-assistant',
      version: 'v2.1.0',
      size: '45 MB',
      category: 'ia produtividade',
      description: 'Assistente virtual baseado em inteligência artificial para atendimento ao cidadão e suporte aos servidores municipais.'
    },
    {
      id: 'curriculo-chatbot',
      title: 'Currículo-Chatbot',
      version: 'v1.3.2',
      size: '32 MB',
      category: 'ia produtividade',
      description: 'Ferramenta para análise automática de currículos e triagem inicial de candidatos para processos seletivos municipais.'
    },
    {
      id: 'iso-checklist',
      title: 'ISO-Checklist',
      version: 'v2.0.1',
      size: '18 MB',
      category: 'produtividade',
      description: 'Aplicativo para verificação de conformidade com normas ISO em processos e serviços municipais.'
    },
    {
      id: 'templates-email',
      title: 'Templates-Email',
      version: 'v1.5.0',
      size: '15 MB',
      category: 'produtividade',
      description: 'Conjunto de modelos profissionais para comunicação oficial via e-mail, garantindo padronização da comunicação.'
    },
    {
      id: 'analisador-malware',
      title: 'Analisador-Malware',
      version: 'v3.2.1',
      size: '56 MB',
      category: 'seguranca',
      description: 'Ferramenta para detecção e proteção contra software malicioso nos sistemas da prefeitura.'
    },
    {
      id: 'gerador-senhas',
      title: 'Gerador-Senhas',
      version: 'v2.0.3',
      size: '12 MB',
      category: 'seguranca',
      description: 'Aplicativo seguro para criação e gerenciamento de senhas fortes para sistemas municipais, aumentando a segurança digital.'
    },
    {
      id: 'simulador-phishing',
      title: 'Simulador-Phishing',
      version: 'v1.8.5',
      size: '38 MB',
      category: 'seguranca treinamento',
      description: 'Ferramenta educativa para treinar servidores a identificar e evitar ataques de phishing, através de simulações controladas.'
    },
    {
      id: 'analise-dados-dashboard',
      title: 'Análise de Dados (Dashboard)',
      version: 'v2.4.0',
      size: '65 MB',
      category: 'produtividade',
      description: 'Plataforma para visualização e análise de dados municipais, auxiliando na tomada de decisões baseadas em evidências.'
    },
    {
      id: 'rpa-automacao',
      title: 'Robôs (RPA) para Automação',
      version: 'v1.9.3',
      size: '42 MB',
      category: 'produtividade',
      description: 'Soluções de Automação de Processos por Robôs para otimizar tarefas repetitivas e burocráticas da administração municipal.'
    },
    {
      id: 'oficios',
      title: 'Ofícios',
      version: 'v2.1.4',
      size: '25 MB',
      category: 'produtividade',
      description: 'Sistema para geração e gestão eletrônica de ofícios e documentos oficiais da prefeitura, com modelos padronizados.'
    },
    {
      id: 'guia-ia-servidores',
      title: 'Guia sobre IA para Servidores',
      version: 'v1.2.0',
      size: '28 MB',
      category: 'ia treinamento',
      description: 'Manual completo sobre o uso de Inteligência Artificial na administração pública, com exemplos práticos e recomendações.'
    },
    {
      id: 'treinamento-praticas-digitais',
      title: 'Treinamento sobre Boas Práticas Digitais',
      version: 'v1.5.2',
      size: '48 MB',
      category: 'treinamento seguranca',
      description: 'Curso interativo para capacitar servidores em segurança da informação e uso eficiente de recursos digitais.'
    },
    {
      id: 'guia-tratamento-dados',
      title: 'Guia Rápido - Tratamento de Dados',
      version: 'v1.3.1',
      size: '22 MB',
      category: 'treinamento produtividade',
      description: 'Manual prático sobre boas práticas no tratamento de dados pessoais conforme a LGPD, adaptado para a realidade municipal.'
    }
  ];

  // Detectar sistema operacional do usuário através do User-Agent (apenas para informação inicial)
  const userAgent = req.headers['user-agent'] || '';
  const isMac = userAgent.includes('Macintosh') || userAgent.includes('Mac OS X');
  const isWindows = userAgent.includes('Windows');
  const isLinux = userAgent.includes('Linux');
  
  // Definir extensões apropriadas para cada sistema
  let detectedOS = 'unknown';
  if (isMac) {
    detectedOS = 'macos';
  } else if (isWindows) {
    detectedOS = 'windows';
  } else if (isLinux) {
    detectedOS = 'linux';
  }
  
  // Enviar a lista como resposta (sem aplicar extensões ainda, isso será feito no momento do download)
  res.status(200).json({
    success: true,
    count: appsList.length,
    platform: detectedOS,
    apps: appsList
  });
};