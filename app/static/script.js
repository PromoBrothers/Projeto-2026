// /mercado_livre_scraper/app/static/script.js

let supabaseClient = null;
let supabaseInitialized = false;

// Função para mostrar alertas visuais
function showAlert(message, type = 'info') {
  // Remove alertas anteriores
  const existingAlert = document.querySelector('.custom-alert');
  if (existingAlert) {
    existingAlert.remove();
  }

  // Cria o elemento do alerta
  const alert = document.createElement('div');
  alert.className = `custom-alert custom-alert-${type}`;
  
  // Define cores baseadas no tipo
  const colors = {
    'success': { bg: '#d4edda', border: '#c3e6cb', text: '#155724' },
    'error': { bg: '#f8d7da', border: '#f5c6cb', text: '#721c24' },
    'warning': { bg: '#fff3cd', border: '#ffeaa7', text: '#856404' },
    'info': { bg: '#d1ecf1', border: '#bee5eb', text: '#0c5460' }
  };
  
  const color = colors[type] || colors.info;
  
  alert.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 15px 20px;
    background-color: ${color.bg};
    border: 1px solid ${color.border};
    color: ${color.text};
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 10000;
    max-width: 400px;
    font-family: 'Poppins', sans-serif;
    font-size: 14px;
    line-height: 1.4;
    transition: all 0.3s ease;
    cursor: pointer;
  `;
  
  alert.textContent = message;
  document.body.appendChild(alert);
  
  // Remove o alerta ao clicar ou após 5 segundos
  alert.addEventListener('click', () => alert.remove());
  setTimeout(() => {
    if (alert.parentNode) {
      alert.style.opacity = '0';
      alert.style.transform = 'translateX(100%)';
      setTimeout(() => alert.remove(), 300);
    }
  }, 5000);
  
  console.log(`[${type.toUpperCase()}] ${message}`);
}

function initializeSupabase() {
  try {
    const supabaseUrl = localStorage.getItem('supabase_url') || 'https://cfacybymuscwcpgmbjkz.supabase.co';
    const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNmYWN5YnltdXNjd2NwZ21iamt6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NTk1MzY4MSwiZXhwIjoyMDcxNTI5NjgxfQ.6IWnYtV1u0PpUVp72HPbKzel2VTuoLzVEz6IJuuThvs';
    
    if (typeof supabase !== 'undefined') {
      supabaseClient = supabase.createClient(supabaseUrl, supabaseKey);
      supabaseInitialized = true;
      console.log('✅ Supabase Client inicializado com sucesso');
    } else {
      console.warn('⚠️ Supabase JS não foi carregado');
    }
  } catch (error) {
    console.error('❌ Erro ao inicializar Supabase Client:', error);
  }
}

async function downloadImageDirect(filePath, bucketName = null) {
  if (!supabaseInitialized || !supabaseClient) {
    console.log('📡 Fallback: usando API tradicional para imagem');
    return null;
  }

  try {
    const bucket = bucketName || bucketAtual;
    console.log(`🔄 Baixando imagem via Supabase JS: ${filePath} do bucket ${bucket}`);
    
    const { data, error } = await supabaseClient.storage
      .from(bucket)
      .download(filePath);
    
    if (error) {
      console.error('❌ Erro no download direto:', error.message);
      return null;
    }

    const url = URL.createObjectURL(data);
    console.log('✅ Imagem baixada via Supabase JS:', filePath);
    return url;
    
  } catch (error) {
    console.error('❌ Erro ao baixar imagem diretamente:', error.message);
    return null;
  }
}

async function listImagesDirect(bucketName = null, path = '', limit = 20, offset = 0) {
  if (!supabaseInitialized || !supabaseClient) {
    return null;
  }

  try {
    const bucket = bucketName || bucketAtual;
    console.log(`🔍 Listando imagens via Supabase JS do bucket: ${bucket}`);
    
    const { data, error } = await supabaseClient.storage
      .from(bucket)
      .list(path, {
        limit: limit,
        offset: offset,
        sortBy: { column: 'created_at', order: 'desc' }
      });
    
    if (error) {
      console.error('❌ Erro ao listar imagens:', error.message);
      return null;
    }

    const imagens = data
      .filter(file => file.name && !file.name.endsWith('/'))
      .map(file => {
        const publicUrl = supabaseClient.storage
          .from(bucket)
          .getPublicUrl(path + file.name);
        
        return {
          nome: file.name,
          url: publicUrl.data.publicUrl,
          tamanho: file.metadata?.size || 0,
          caminho: path + file.name
        };
      });

    console.log(`✅ ${imagens.length} imagens listadas via Supabase JS`);
    return imagens;
    
  } catch (error) {
    console.error('❌ Erro ao listar imagens via Supabase JS:', error.message);
    return null;
  }
}

// ⭐ NOVA FUNÇÃO: Envia mensagem e imagem geradas para o serviço Baileys via proxy Flask
async function sendGeneratedMessage(message, imageUrl) {
    // Note: Removemos o controle de "loading" daqui para evitar conflito com loops
    try {
        const response = await fetch('/whatsapp/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                imageUrl: imageUrl
            })
        });

        const data = await response.json();
        
        if (response.ok && data.success) {
            console.log('✅ Mensagem enviada com sucesso via Baileys!');
            return { success: true, message: data.message };
        } else {
            const errorMsg = data.error || 'Erro desconhecido no envio Baileys';
            console.error(`❌ Falha no envio: ${errorMsg}`);
            // Retorna o erro e a resposta completa para o log no console
            return { success: false, error: errorMsg, response: data }; 
        }

    } catch (error) {
        console.error('Erro de rede ao tentar enviar via Baileys:', error);
        return { success: false, error: 'Erro de conexão de rede.' };
    }
}


window.openAgendamentoForm = function (produtoId) {
  document.getElementById("agendarProdutoId").value = produtoId;
  document.getElementById("agendamentoModal").style.display = "block";
};

window.closeModal = function () {
  document.getElementById("agendamentoModal").style.display = "none";
};

window.openEditarForm = function (produtoId) {
  document.getElementById("editarProdutoId").value = produtoId;

  document.getElementById("editarImagemUrl").value = "";
  document.getElementById("editarMensagem").value = "";
  
  // Limpar campos de cupom
  if (document.getElementById("cupomTexto")) {
    document.getElementById("cupomTexto").value = "";
    document.getElementById("cupomValor").value = "";
    document.getElementById("cupomLimite").value = "";
    document.getElementById("cupomId").value = "";
    document.getElementById("cupomTipo").value = "porcentagem";

    // Resetar select de cupom
    const cupomSelect = document.getElementById("cupomSelect");
    if (cupomSelect) {
      cupomSelect.value = "";
    }

    // Limpar preview
    const cupomPreview = document.getElementById("cupomPreview");
    if (cupomPreview) {
      cupomPreview.style.display = "none";
      cupomPreview.innerHTML = "";
    }
  }

  updateImagePreview();

  fetch(`/produtos/${produtoId}`, { method: "GET" })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        const produto = data.produto;

        produtoAtualData = produto;

        console.log('📦 Produto carregado:', {
          preco_atual: produto.preco_atual,
          preco_original: produto.preco_original,
          preco_promocional: produto.preco_promocional,
          preco_com_cupom: produto.preco_com_cupom
        });

        document.getElementById("editarImagemUrl").value =
          produto.imagem_url || "";
        document.getElementById("editarMensagem").value =
          produto.final_message || "";

        updateImagePreview();
      }
    })
    .catch((error) => {
      console.error("Erro ao carregar dados do produto:", error);
      produtoAtualData = null;
    });

  document.getElementById("editarModal").style.display = "block";
};

window.closeEditModal = function () {
  document.getElementById("editarModal").style.display = "none";
  produtoAtualData = null;
};

window.enviarProdutoAgendado = async function (produtoId) {
  if (
    !confirm(
      "Deseja gerar e ENVIAR a mensagem final deste produto para o WhatsApp?" // Texto atualizado
    )
  ) {
    return;
  }

  const loading = document.getElementById("loading");
  loading.style.display = "block";
  loading.querySelector("p").textContent = "Gerando mensagem final..."; // Texto atualizado

  try {
    const afiliadoLink = prompt("Cole o link de afiliado (opcional):");

    const response = await fetch(`/enviar_produto_agendado/${produtoId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        afiliado_link: afiliadoLink || "",
      }),
    });

    const data = await response.json();

    if (response.ok) {
      // Mensagem gerada com sucesso
      showAlert("Mensagem gerada com sucesso! ✅", "success");

      if (data.final_message) {
        // Exibir a mensagem gerada
        displayWebhookResponse(data.final_message, 'success', data.image_url);

        // ⭐ NOVO PASSO: Enviar a mensagem gerada via Baileys
        const sendResult = await sendGeneratedMessage(data.final_message, data.image_url);
        
        if (sendResult.success) {
            showAlert("✅ Envio para o WhatsApp concluído!", "success");
        } else {
            showAlert(`⚠️ Mensagem gerada, mas falha no envio: ${sendResult.error}`, "warning");
        }
      }
    } else {
      showAlert(`Erro ao gerar mensagem: ${data.error}`, "error"); // Mensagem atualizada
    }
  } catch (error) {
    console.error("Erro ao gerar mensagem:", error);
    showAlert("Erro de conexão ao gerar mensagem.", "error");
  } finally {
    loading.style.display = "none";
  }
};

function displayWebhookResponse(message, status, imageUrl, append = false) {
    const webhookMessageSection = document.getElementById("webhookMessageSection");
    const webhookMessageContent = document.getElementById("webhookMessageContent");
    if (!webhookMessageSection || !webhookMessageContent) return;

    let imageHtml = "";
    if (imageUrl && imageUrl.trim()) {
        imageHtml = `<div class="webhook-image"><img src="${imageUrl}" alt="Imagem do Produto"></div>`;
    }

    const isSuccess = status === 'success';
    const containerClass = isSuccess ? 'success' : 'error';
    // O texto do header é atualizado para refletir o novo fluxo (processamento/geração)
    const headerText = isSuccess ? '✅ Produto Processado (Mensagem Gerada)' : '❌ Erro ao Processar';
    const statusText = isSuccess ? 'SUCCESS' : 'ERROR';

    const messageHtml = `
        <div class="webhook-message-container ${containerClass}" style="margin-bottom: 20px;">
            <div class="webhook-message-header">
                <h3>${headerText}</h3>
                <span class="status ${containerClass}">${statusText}</span>
            </div>
            ${imageHtml}
            <pre>${message}</pre>
        </div>
    `;

    if (append) {
        webhookMessageContent.insertAdjacentHTML('beforeend', messageHtml);
    } else {
        webhookMessageContent.innerHTML = messageHtml;
    }
    
    webhookMessageSection.style.display = "block";
    webhookMessageSection.scrollIntoView({ behavior: "smooth" });
}


window.updateImagePreview = function () {
  const imageUrl = document.getElementById("editarImagemUrl").value.trim();
  const imagePreview = document.getElementById("imagePreview");
  const placeholder = document.getElementById("imagePreviewPlaceholder");

  if (!imagePreview || !placeholder) return;

  if (imageUrl && isValidImageUrl(imageUrl)) {
    imagePreview.src = imageUrl;
    imagePreview.style.display = "block";
    placeholder.style.display = "none";

    imagePreview.onload = function () {
      imagePreview.style.display = "block";
      placeholder.style.display = "none";
    };

    imagePreview.onerror = function () {
      imagePreview.style.display = "none";
      placeholder.style.display = "block";
      placeholder.innerHTML = "❌ Erro ao carregar imagem";
    };
  } else {
    imagePreview.style.display = "none";
    placeholder.style.display = "block";
    if (imageUrl && !isValidImageUrl(imageUrl)) {
      placeholder.innerHTML = "⚠️ URL de imagem inválida";
    } else {
      placeholder.innerHTML = "📷 Nenhuma imagem para mostrar";
    }
  }
};

let produtoAtualData = null;

window.alterarTipoCupom = function () {
  const cupomTipo = document.getElementById("cupomTipo").value;
  const cupomValorLabel = document.getElementById("cupomValorLabel");
  const cupomValorInput = document.getElementById("cupomValor");

  if (cupomTipo === "porcentagem") {
    cupomValorLabel.textContent = "Desconto (%)";
    cupomValorInput.placeholder = "10";
    cupomValorInput.max = "99";
    cupomValorInput.step = "1";
  } else {
    cupomValorLabel.textContent = "Desconto (R$)";
    cupomValorInput.placeholder = "60.00";
    cupomValorInput.removeAttribute("max");
    cupomValorInput.step = "0.01";
  }
  
  cupomValorInput.value = "";
};

window.calcularDesconto = function () {
  const cupomTexto = document.getElementById("cupomTexto").value.trim();
  const cupomTipo = document.getElementById("cupomTipo").value;
  const cupomValor = parseFloat(document.getElementById("cupomValor").value);
  const cupomPreview = document.getElementById("cupomPreview");
  const cupomInfo = document.getElementById("cupomInfo");

  if (!cupomTexto || !cupomValor || cupomValor <= 0) {
    cupomPreview.style.display = "none";
    return;
  }

  if (cupomTipo === "porcentagem" && (cupomValor < 1 || cupomValor > 99)) {
    cupomPreview.style.display = "none";
    return;
  }

  if (produtoAtualData && produtoAtualData.preco_atual) {
    const precoOriginal = extrairValorNumerico(produtoAtualData.preco_atual);
    if (precoOriginal > 0) {
      let desconto, novoPreco, cupomDescricao;
      
      if (cupomTipo === "porcentagem") {
        desconto = (precoOriginal * cupomValor) / 100;
        cupomDescricao = `${cupomTexto} (-${cupomValor}%)`;
      } else {
        desconto = cupomValor;
        const valorFmt = cupomValor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        cupomDescricao = `${cupomTexto} (-R$ ${valorFmt})`;
      }
      
      novoPreco = Math.max(0, precoOriginal - desconto);
      
      const precoOriginalFmt = precoOriginal.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      const descontoFmt = desconto.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      const novoPrecoFmt = novoPreco.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

      cupomInfo.innerHTML = `
        <div style="display: grid; grid-template-columns: auto auto; gap: 12px; align-items: center;">
          <span>💰 Preço Original:</span>
          <span style="font-weight: 500;">R$ ${precoOriginalFmt}</span>
          <span>🎟️ Cupom:</span>
          <span style="font-weight: 500; color: #ff6b6b;">${cupomDescricao}</span>
          <span>💸 Desconto:</span>
          <span style="font-weight: 500; color: #28a745;">-R$ ${descontoFmt}</span>
          <span>🏷️ <strong>Preço Final:</strong></span>
          <span style="font-weight: 700; color: #007bff; font-size: 16px;">R$ ${novoPrecoFmt}</span>
        </div>
      `;
      cupomPreview.style.display = "block";
    } else {
      cupomPreview.style.display = "none";
    }
  } else {
    cupomInfo.innerHTML = `
      <div style="color: #666; font-style: italic;">
        ℹ️ Preview será calculado com base no preço do produto
      </div>
    `;
    cupomPreview.style.display = "block";
  }
};

window.aplicarCupom = function () {
  const cupomTexto = document.getElementById("cupomTexto").value.trim();
  const cupomTipo = document.getElementById("cupomTipo").value;
  const cupomValor = parseFloat(document.getElementById("cupomValor").value);
  const cupomLinkAfiliado = document.getElementById("cupomLinkAfiliado").value.trim();
  const mensagemTextarea = document.getElementById("editarMensagem");

  if (!cupomTexto || !cupomValor || cupomValor <= 0) {
    showAlert("Por favor, preencha o texto do cupom e um valor válido", "error");
    return;
  }

  if (cupomTipo === "porcentagem" && (cupomValor < 1 || cupomValor > 99)) {
    showAlert("Porcentagem deve estar entre 1% e 99%", "error");
    return;
  }

  if (!produtoAtualData) {
    showAlert("Erro: dados do produto não encontrados", "error");
    return;
  }

  const precoOriginal = extrairValorNumerico(produtoAtualData.preco_atual);
  if (precoOriginal <= 0) {
    showAlert("Erro: não foi possível extrair o preço do produto", "error");
    return;
  }

  let desconto, novoPreco;
  if (cupomTipo === "porcentagem") {
    desconto = (precoOriginal * cupomValor) / 100;
  } else {
    desconto = cupomValor;
  }
  
  novoPreco = Math.max(0, precoOriginal - desconto);
  const novoPrecoFormatado = `R$ ${novoPreco.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  const mensagemComCupom = construirMensagemComCupom(produtoAtualData, cupomTexto, cupomTipo, cupomValor, precoOriginal, novoPreco, desconto, cupomLinkAfiliado);
  
  mensagemTextarea.value = mensagemComCupom;
  
  produtoAtualData.cupom_aplicado = {
    texto: cupomTexto,
    tipo: cupomTipo,
    valor: cupomValor,
    preco_original: produtoAtualData.preco_atual,
    preco_novo: novoPrecoFormatado,
    desconto: desconto,
    link_afiliado: cupomLinkAfiliado
  };
  
  document.getElementById("cupomTexto").value = "";
  document.getElementById("cupomValor").value = "";
  document.getElementById("cupomLinkAfiliado").value = "";
  document.getElementById("cupomPreview").style.display = "none";
  document.getElementById("cupomTipo").value = "porcentagem";
  alterarTipoCupom();

  const tipoDescricao = cupomTipo === "porcentagem" ? `${cupomValor}%` : `R$ ${cupomValor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  showAlert(`🎉 Cupom ${cupomTexto} (${tipoDescricao}) aplicado! Preço atualizado para ${novoPrecoFormatado}. Salve as alterações para confirmar.`, "success");
};

function extrairValorNumerico(precoTexto) {
  if (!precoTexto) return 0;
  
  const numeroLimpo = precoTexto.toString()
    .replace(/R\$/g, '')
    .replace(/\s/g, '')
    .replace(/[^\d,.]/g, '');
  
  if (numeroLimpo.includes('.') && numeroLimpo.includes(',')) {
    const valor = parseFloat(numeroLimpo.replace(/\./g, '').replace(',', '.'));
    return isNaN(valor) ? 0 : valor;
  }
  
  if (numeroLimpo.includes(',') && !numeroLimpo.includes('.')) {
    const valor = parseFloat(numeroLimpo.replace(',', '.'));
    return isNaN(valor) ? 0 : valor;
  }
  
  if (numeroLimpo.includes('.')) {
    const partes = numeroLimpo.split('.');
    if (partes.length === 2 && partes[1].length <= 2) {
      const valor = parseFloat(numeroLimpo);
      return isNaN(valor) ? 0 : valor;
    } else {
      const valor = parseFloat(numeroLimpo.replace(/\./g, ''));
      return isNaN(valor) ? 0 : valor;
    }
  }
  
  const valor = parseFloat(numeroLimpo);
  return isNaN(valor) ? 0 : valor;
}

function construirMensagemComCupom(produto, cupomTexto, cupomTipo, cupomValor, precoOriginal, novoPreco, desconto, linkAfiliado) {
  const linkProduto = linkAfiliado || produto.afiliado_link || produto.link_produto || produto.link || 'Link não disponível';
  const vendedor_info = produto.vendedor || produto.condicao || '* Informação não disponível';

  const precoOriginalFmt = precoOriginal.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const novoPrecoFmt = novoPreco.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  
  const precoOriginalComRS = `R$ ${precoOriginalFmt}`;
  const novoPrecoComRS = `R$ ${novoPrecoFmt}`;

  // Usando o novo padrão de mensagem
  return `🔥 *${produto.titulo}*
* _${vendedor_info}_

✅ De ~${precoOriginalComRS}~ → *Por ${novoPrecoComRS}*
🎟️ *Cupom: ${cupomTexto}*
🛒 ${linkProduto}

👥 Link do grupo: https://linktr.ee/promobrothers.shop `;

}

function isValidImageUrl(url) {
  try {
    new URL(url);
    const imageExtensions = /\.(jpg|jpeg|png|gif|webp|svg|bmp)(\?.*)?$/i;
    const knownImageDomains = /(mlstatic\.com|imgur\.com|cloudinary\.com)/i;
    return (
      imageExtensions.test(url) ||
      knownImageDomains.test(url) ||
      url.includes("http")
    );
  } catch {
    return false;
  }
}

window.deletarAgendamento = async function (produtoId, buttonElement) {
  if (!confirm("Tem certeza que deseja excluir este produto?")) {
    return;
  }

  const cardParaRemover = buttonElement.closest(".product-card");

  if (cardParaRemover) {
    cardParaRemover.style.transition = "opacity 0.3s ease-out";
    cardParaRemover.style.opacity = "0";
    setTimeout(() => cardParaRemover.remove(), 300);
  }

  try {
    const response = await fetch(`/produtos/${produtoId}`, {
      method: "DELETE",
    });

    const data = await response.json();

    if (response.ok) {
      showAlert(data.message, "success");
    } else {
      showAlert(data.error || "Erro ao excluir o produto.", "error");
      loadAgendamentos();
    }
  } catch (error) {
    showAlert("Erro de conexão ao tentar excluir o produto.", "error");
    loadAgendamentos();
  }
};

function createAgendamentoCard(produto) {
    const card = document.createElement("div");
    card.className = "product-card";

    let dataInfo = produto.agendamento ? `Agendado para: <b>${produto.agendamento}</b>` : `Criado em: <b>${produto.created_at || "N/A"}</b>`;
    const imagemParaUsar = produto.imagem_url || produto.processed_image_url || "";
    const imagemComCache = imagemParaUsar ? `${imagemParaUsar}?t=${Date.now()}` : "";

    let platformBadge = '';
    if (produto.fonte) {
        platformBadge = `<div class="platform-badge" data-platform="${produto.fonte}">${produto.fonte}</div>`;
    }

    let precoFormatado = produto.preco_atual || '';
    if (precoFormatado && !precoFormatado.toString().includes('R$')) {
        precoFormatado = `R$ ${precoFormatado}`;
    }

    card.innerHTML = `
        <div class="product-header">
          <img src="${imagemComCache}" alt="${produto.titulo}" class="product-image">
          ${platformBadge}
          <div class="product-info">
            <div class="product-title">${produto.titulo}</div>
            <div class="product-price-atual">${precoFormatado}</div>
          </div>
        </div>
        <p>${dataInfo}</p>
        <div class="product-actions">
            <button class="btn btn-reagendar" onclick="openAgendamentoForm('${produto.id}')">${produto.agendamento ? 'Reagendar' : 'Agendar'}</button>
            <button class="btn btn-editar" onclick="openEditarForm('${produto.id}')">Editar</button>
            <button class="btn btn-primary" onclick="abrirModalEnvio('${produto.id}')" style="background: linear-gradient(135deg, #25d366 0%, #128c7e 100%); border: none;">📤 Enviar Agora</button>
            <button class="btn btn-excluir" onclick="deletarAgendamento('${produto.id}', this)">Excluir</button>
        </div>
      `;
    return card;
}

// Cache para otimização de carregamento
let lastLoadTime = 0;
let lastLoadedData = null;
const CACHE_DURATION = 5000; // 5 segundos de cache

async function loadAgendamentos(forceRefresh = false) {
  const agendamentoList = document.getElementById("agendamento-list");
  if (!agendamentoList) return;

  const status = document.getElementById("filtroStatus").value;
  const ordem = document.getElementById("filtroOrdem").value;

  // 🔥 OTIMIZAÇÃO: Usar cache se não forçar refresh e cache ainda válido
  const now = Date.now();
  if (!forceRefresh && lastLoadedData && (now - lastLoadTime) < CACHE_DURATION) {
    console.log('✅ Usando cache de produtos (mais rápido)');
    renderProducts(lastLoadedData.produtos);
    return;
  }

  // Mostrar indicador de carregamento suave
  if (!agendamentoList.querySelector('.loading-indicator')) {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading-indicator';
    loadingDiv.innerHTML = '<p style="color: #667eea; text-align: center;">⏳ Carregando produtos...</p>';
    agendamentoList.innerHTML = '';
    agendamentoList.appendChild(loadingDiv);
  }

  try {
    const startTime = performance.now();
    const response = await fetch(`/produtos?status=${status}&ordem=${ordem}`);
    const data = await response.json();
    const loadTime = (performance.now() - startTime).toFixed(0);

    console.log(`📊 Produtos carregados em ${loadTime}ms`);

    if (data.success) {
      // Atualizar cache
      lastLoadedData = data;
      lastLoadTime = Date.now();

      renderProducts(data.produtos);
    } else {
      throw new Error(data.error);
    }
  } catch (error) {
    console.error("Erro ao carregar agendamentos:", error);
    agendamentoList.innerHTML = `<p style="color: #e74c3c;">Erro ao carregar produtos: ${error.message}</p>`;
  }
}

// Função auxiliar para renderizar produtos
function renderProducts(produtos) {
  const agendamentoList = document.getElementById("agendamento-list");
  if (!agendamentoList) return;

  if (produtos.length > 0) {
    agendamentoList.innerHTML = "";
    // Usar DocumentFragment para performance
    const fragment = document.createDocumentFragment();
    produtos.forEach((produto) => {
      const card = createAgendamentoCard(produto);
      fragment.appendChild(card);
    });
    agendamentoList.appendChild(fragment);
  } else {
    agendamentoList.innerHTML = "<p>Nenhum produto encontrado com os filtros selecionados.</p>";
  }
}

document.addEventListener("DOMContentLoaded", function () {
  initializeSupabase();
  
  const themeToggle = document.getElementById("themeToggle");
  const savedTheme = localStorage.getItem("theme") || "light";
  
  if (savedTheme === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
    themeToggle.textContent = "☀️";
  } else {
    themeToggle.textContent = "🌙";
  }
  
  themeToggle.addEventListener("click", function() {
    const currentTheme = document.documentElement.getAttribute("data-theme");
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    
    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);
    
    showAlert(
      `Modo ${newTheme === "dark" ? "escuro" : "claro"} ativado!`,
      "info"
    );
  });

  const searchForm = document.getElementById("searchForm");
  const linkForm = document.getElementById("linkForm");
  const webhookForm = document.getElementById("webhookForm");
  const loading = document.getElementById("loading");
  const resultsSection = document.getElementById("resultsSection");
  const produtoSection = document.getElementById("produtoSection");
  const productsGrid = document.getElementById("productsGrid");
  const produtoDetalhado = document.getElementById("produtoDetalhado");
  const resultsCount = document.getElementById("resultsCount");
  const clearBtn = document.getElementById("clearBtn");
  const clearProdutoBtn = document.getElementById("clearProdutoBtn");
  const webhookMessageSection = document.getElementById(
    "webhookMessageSection"
  );
  const webhookMessageContent = document.getElementById(
    "webhookMessageContent"
  );
  const clearWebhookBtn = document.getElementById("clearWebhookBtn");
  const searchBtn = document.getElementById("searchBtn");
  const linkBtn = document.getElementById("linkBtn");
  const webhookBtn = document.getElementById("webhookBtn");
  const editarForm = document.getElementById("editarForm");

  let productQueue = [];
  
  const inputMethods = document.querySelectorAll('.input-method');
  const inputContents = document.querySelectorAll('.input-content');
  const addProductBtn = document.getElementById('addProductBtn');
  const productUrlInput = document.getElementById('productUrl');
  const queueList = document.getElementById('queueList');
  const queueCount = document.querySelector('.queue-count');
  const processCount = document.getElementById('processCount');
  const clearQueueBtn = document.getElementById('clearQueueBtn');
  const importFromBulkBtn = document.getElementById('importFromBulkBtn');

  const clearWebhookTextareaBtn = document.getElementById(
    "clearWebhookTextareaBtn"
  );
  const webhookUrlsTextarea = document.getElementById("webhookUrls");

  if(clearWebhookTextareaBtn) {
    clearWebhookTextareaBtn.addEventListener("click", function () {
        webhookUrlsTextarea.value = "";
        webhookUrlsTextarea.focus();
    });
  }

  if(inputMethods.length > 0) {
    inputMethods.forEach(method => {
        method.addEventListener('click', () => {
        const methodType = method.dataset.method;
        
        inputMethods.forEach(m => m.classList.remove('active'));
        inputContents.forEach(c => c.classList.remove('active'));
        
        method.classList.add('active');
        document.querySelector(`.${methodType}-mode`).classList.add('active');
        });
    });
  }

  if(addProductBtn) {
    addProductBtn.addEventListener('click', () => {
        const productUrl = productUrlInput.value.trim();

        if (!productUrl) {
        showAlert('Por favor, insira um link de produto ou link de afiliado', 'error');
        return;
        }

        if (!productUrl.includes('mercadolivre.com') && !productUrl.includes('mercadolibre.com')) {
        showAlert('Por favor, use um link válido do Mercado Livre', 'error');
        return;
        }

        const exists = productQueue.some(item => item.productUrl === productUrl);
        if (exists) {
        showAlert('Este produto já está na fila', 'warning');
        return;
        }

        productQueue.push({
        id: Date.now(),
        productUrl: productUrl,
        addedAt: new Date().toLocaleTimeString()
        });

        updateQueueDisplay();

        productUrlInput.value = '';
        productUrlInput.focus();

        showAlert('Produto adicionado à fila!', 'success');
    });
  }

  if(importFromBulkBtn) {
    importFromBulkBtn.addEventListener('click', () => {
        const urlsText = webhookUrlsTextarea.value.trim();
        const lines = urlsText.split('\n').filter(line => line.trim() !== '');

        if (lines.length === 0) {
        showAlert('Nenhum link encontrado para importar', 'error');
        return;
        }

        let imported = 0;
        lines.forEach(line => {
        const productUrl = line.trim();

        if (productUrl && (productUrl.includes('mercadolivre.com') || productUrl.includes('mercadolibre.com'))) {
            const exists = productQueue.some(item => item.productUrl === productUrl);
            if (!exists) {
            productQueue.push({
                id: Date.now() + imported,
                productUrl: productUrl,
                addedAt: new Date().toLocaleTimeString()
            });
            imported++;
            }
        }
        });

        updateQueueDisplay();

        if (imported > 0) {
        showAlert(`${imported} produtos importados para a fila!`, 'success');
        document.querySelector('[data-method="visual"]').click();
        } else {
        showAlert('Nenhum produto válido foi importado', 'warning');
        }
    });
  }
  
  if(clearQueueBtn) {
    clearQueueBtn.addEventListener('click', () => {
        if (productQueue.length === 0) return;
        
        if (confirm('Deseja limpar toda a fila de produtos?')) {
        productQueue = [];
        updateQueueDisplay();
        showAlert('Fila limpa!', 'info');
        }
    });
  }

  function updateQueueDisplay() {
    if(!queueList) return;
    queueCount.textContent = `(${productQueue.length})`;
    processCount.textContent = productQueue.length;

    if (productQueue.length === 0) {
      queueList.innerHTML = `
        <div class="queue-empty">
          <span class="empty-icon">📦</span>
          <p>Nenhum produto na fila</p>
          <small>Adicione produtos usando o formulário acima</small>
        </div>
      `;
      return;
    }

    queueList.innerHTML = productQueue.map(item => `
      <div class="queue-item" data-id="${item.id}">
        <div class="queue-item-icon">🛒</div>
        <div class="queue-item-content">
          <div class="queue-item-title">
            ${item.productUrl.length > 60 ? item.productUrl.substring(0, 60) + '...' : item.productUrl}
          </div>
          <div class="queue-item-subtitle">
            Adicionado às ${item.addedAt}
          </div>
        </div>
        <div class="queue-item-actions">
          <button class="remove-item-btn" onclick="removeFromQueue(${item.id})">
            🗑️ Remover
          </button>
        </div>
      </div>
    `).join('');
  }

  window.removeFromQueue = function(id) {
    productQueue = productQueue.filter(item => item.id !== id);
    updateQueueDisplay();
    showAlert('Produto removido da fila', 'info');
  };

  if(queueList) {
    updateQueueDisplay();
  }

  const filtroAgendamentoForm = document.getElementById(
    "filtroAgendamentoForm"
  );
  const aplicarFiltroBtn = document.getElementById("aplicarFiltroBtn");

  window.showTab = function (tabName, element) {
    document.querySelectorAll(".tab-content").forEach((tab) => {
      tab.classList.remove("active");
    });
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.classList.remove("active");
    });

    document.getElementById("tab-" + tabName).classList.add("active");
    element.classList.add("active");

    if (resultsSection) resultsSection.style.display = "none";
    if (produtoSection) produtoSection.style.display = "none";
    if (webhookMessageSection) webhookMessageSection.style.display = "none";
    if (loading) loading.style.display = "none";

    if (tabName === "agendamento") {
      loadAgendamentos();
    }
  };

  if(searchForm) {
    searchForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        const produto = document.getElementById("produto").value.trim();
        const maxPages = parseInt(document.getElementById("maxPages").value);

        if (!produto) {
        showAlert("Por favor, digite um produto para buscar", "error");
        return;
        }

        loading.style.display = "block";
        loading.querySelector("p").textContent =
        "Buscando produtos no Mercado Livre...";
        resultsSection.style.display = "none";
        produtoSection.style.display = "none";
        webhookMessageSection.style.display = "none";
        searchBtn.disabled = true;

        try {
        const response = await fetch("/buscar", {
            method: "POST",
            headers: {
            "Content-Type": "application/json",
            },
            body: JSON.stringify({
            produto: produto,
            max_pages: maxPages,
            }),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Erro HTTP: ${response.status} - ${errorText}`);
        }

        const data = await response.json();

        if (data.success) {
            displayResults(data.resultados, data.total);
        } else {
            showAlert(data.error || "Erro desconhecido", "error");
        }
        } catch (error) {
        console.error("Erro detalhado:", error);
        showAlert("Erro de conexão: " + error.message, "error");
        } finally {
        loading.style.display = "none";
        searchBtn.disabled = false;
        }
    });
  }

  if(linkForm) {
    linkForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        const url = document.getElementById("produtoUrl").value.trim();

        if (!url) {
        showAlert("Por favor, cole o link do produto", "error");
        return;
        }

        if (
        !url.includes("mercadolivre.com") &&
        !url.includes("mercadolibre.com")
        ) {
        showAlert("Por favor, use um link válido do Mercado Livre", "error");
        return;
        }

        loading.style.display = "block";
        loading.querySelector("p").textContent = "Analisando o produto...";
        resultsSection.style.display = "none";
        produtoSection.style.display = "none";
        webhookMessageSection.style.display = "none";
        linkBtn.disabled = true;

        try {
        const response = await fetch("/produto", {
            method: "POST",
            headers: {
            "Content-Type": "application/json",
            },
            body: JSON.stringify({
            url: url,
            }),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Erro HTTP: ${response.status} - ${errorText}`);
        }

        const data = await response.json();

        if (data.success) {
            displayProdutoDetalhado(data.produto);
        } else {
            showAlert(data.error || "Erro desconhecido", "error");
        }
        } catch (error) {
        console.error("Erro detalhado:", error);
        showAlert("Erro de conexão: " + error.message, "error");
        } finally {
        loading.style.display = "none";
        linkBtn.disabled = false;
        }
    });
  }

  if(webhookForm) {
    webhookForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        let itemsToProcess = [];

        if (productQueue.length > 0) {
        itemsToProcess = productQueue.map(item => ({
            productUrl: item.productUrl,
            affiliateLink: ''
        }));
        } else {
        const urlsText = document.getElementById("webhookUrls").value.trim();
        const lines = urlsText.split("\n").filter((line) => line.trim() !== "");

        if (lines.length === 0) {
            showAlert("Por favor, adicione produtos à fila ou cole links no modo massa", "error");
            return;
        }

        itemsToProcess = lines.map(line => {
            return {
            productUrl: line.trim(),
            affiliateLink: ''
            };
        });
        }

        loading.style.display = "block";
        webhookMessageSection.style.display = "none";
        webhookBtn.disabled = true;

        webhookMessageContent.innerHTML = "";
        webhookMessageSection.style.display = "block";

        let totalProcessedCount = 0;

        for (let i = 0; i < itemsToProcess.length; i++) {
        const { productUrl, affiliateLink } = itemsToProcess[i];

        loading.querySelector("p").textContent = `Processando ${i + 1} de ${
            itemsToProcess.length
        }: ${productUrl.substring(0, 50)}...`;

        if (
            !productUrl.includes("mercadolivre.com") &&
            !productUrl.includes("mercadolibre.com")
        ) {
            displayWebhookResponse(
            `Item ${i + 1}: Link de produto inválido.`,
            "error",
            null,
            true
            );
            continue;
        }

        try {
            // 1. ANÁLISE DO PRODUTO
            const produtoResponse = await fetch("/produto", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: productUrl }),
            });

            if (!produtoResponse.ok)
            throw new Error(`Falha ao buscar dados do produto`);

            const produtoData = await produtoResponse.json();
            const produto = produtoData.produto;

            if (!produto) throw new Error(`Não foi possível extrair dados`);

            // 2. CHAMA O NOVO ENDPOINT DE PROCESSAMENTO (Gera Mensagem e Salva)
            const payload = {
            type: "produto",
            produto: produto,
            afiliado_link: affiliateLink,
            };

            const finalResponse = await fetch("/processar_para_envio", { 
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
            });

            const finalResult = await finalResponse.json();

            if (finalResponse.ok) {
                totalProcessedCount++;
                const message = finalResult.final_message || "Mensagem gerada com sucesso!";
                const imageUrl = finalResult.image_url || produto.imagem;

                // Mensagem gerada: Exibir o resultado
                displayWebhookResponse(
                    message,
                    "success",
                    imageUrl,
                    true
                );
                
                // ⭐ NOVO PASSO: Enviar a mensagem gerada via Baileys
                loading.querySelector("p").textContent = `Enviando ${i + 1} de ${itemsToProcess.length} para o WhatsApp...`;

                const sendResult = await sendGeneratedMessage(message, imageUrl);

                if (sendResult.success) {
                    console.log(`✅ Produto ${i + 1} enviado com sucesso via Baileys.`);
                } else {
                    console.error(`❌ Produto ${i + 1} falhou no envio via Baileys: ${sendResult.error}`);
                    showAlert(`Falha no envio do produto ${i + 1} para o WhatsApp.`, "error");
                }

            } else {
            // Em caso de erro interno (falha na geração/salvamento)
            displayWebhookResponse(
                finalResult.error || "Erro no processamento interno",
                "error",
                finalResult.image_url || produto.imagem,
                true
            );
            }
        } catch (error) {
            console.error("Erro no processo do webhook:", error);
            // Em caso de erro de conexão/parsing
            displayWebhookResponse(
            `Erro ao processar ${productUrl}: ${error.message}`,
            "error",
            null,
            true
            );
        }
        }

        if (productQueue.length > 0) {
        productQueue = [];
        updateQueueDisplay();
        }

        loading.querySelector("p").textContent = `Processamento finalizado! ${totalProcessedCount} produtos processados.`;
        webhookBtn.disabled = false;
        
        setTimeout(() => {
        loading.style.display = "none";
        }, 2000);
    });
  }
    
    if (document.getElementById('amazonSearchForm')) {
        let amazonProductQueue = [];

        const amazonAddProductBtn = document.getElementById('amazonAddProductBtn');
        const amazonClearQueueBtn = document.getElementById('amazonClearQueueBtn');
        const amazonWebhookForm = document.getElementById('amazonWebhookForm');

        function adicionarProdutoFilaAmazon() {
            const productUrlInput = document.getElementById('amazonProductUrlQueue');
            const affiliateUrlInput = document.getElementById('amazonAffiliateUrlQueue');
            if (!productUrlInput || !affiliateUrlInput) return;

            const productUrl = productUrlInput.value.trim();
            const affiliateUrl = affiliateUrlInput.value.trim();

            if (!productUrl) {
                showAlert('Por favor, adicione o link do produto da Amazon', 'error');
                return;
            }
            if (!productUrl.includes('amazon.com') && !productUrl.includes('amzn.to')) {
                showAlert('Por favor, adicione um link válido da Amazon', 'error');
                return;
            }
            if (amazonProductQueue.some(p => p.productUrl === productUrl)) {
                showAlert('Este produto já está na fila', 'warning');
                return;
            }

            amazonProductQueue.push({
                id: Date.now(),
                productUrl: productUrl,
                affiliateUrl: affiliateUrl,
                addedAt: new Date().toLocaleTimeString()
            });
            
            atualizarFilaVisualAmazon();
            productUrlInput.value = '';
            affiliateUrlInput.value = '';
            productUrlInput.focus();
            showAlert('Produto da Amazon adicionado à fila!', 'success');
        }

        function atualizarFilaVisualAmazon() {
            const queueList = document.getElementById('amazonQueueList');
            const queueCount = document.getElementById('amazonQueueCount');
            const processCount = document.getElementById('amazonProcessCount');
            if (!queueList || !queueCount || !processCount) return;
            
            queueCount.textContent = `(${amazonProductQueue.length})`;
            processCount.textContent = amazonProductQueue.length;

            if (amazonProductQueue.length === 0) {
                queueList.innerHTML = `<div class="queue-empty"><span class="empty-icon">📦</span><p>Nenhum produto na fila</p><small>Adicione produtos da Amazon acima</small></div>`;
            } else {
                queueList.innerHTML = amazonProductQueue.map(item => `
                <div class="queue-item" data-id="${item.id}">
                    <div class="queue-item-icon">📦</div>
                    <div class="queue-item-content">
                    <div class="queue-item-title">${item.productUrl.length > 60 ? item.productUrl.substring(0, 60) + '...' : item.productUrl}</div>
                    <div class="queue-item-subtitle">${item.affiliateUrl ? `Afiliado: ${item.affiliateUrl.length > 40 ? item.affiliateUrl.substring(0, 40) + '...' : item.affiliateUrl}` : 'Sem link de afiliado'} • ${item.addedAt}</div>
                    </div>
                    <div class="queue-item-actions">
                    <button class="remove-item-btn" onclick="removerProdutoFilaAmazon(${item.id})">🗑️ Remover</button>
                    </div>
                </div>
                `).join('');
            }
        }

        window.removerProdutoFilaAmazon = function(id) {
            amazonProductQueue = amazonProductQueue.filter(item => item.id !== id);
            atualizarFilaVisualAmazon();
            showAlert('Produto removido da fila', 'info');
        };

        function limparFilaAmazon() {
            if (amazonProductQueue.length > 0 && confirm('Deseja limpar toda a fila de produtos da Amazon?')) {
                amazonProductQueue = [];
                atualizarFilaVisualAmazon();
                showAlert('Fila da Amazon limpa!', 'info');
            }
        }

        async function processarFilaAmazon() {
            if (amazonProductQueue.length === 0) {
                showAlert("Adicione produtos da Amazon à fila antes de processar.", "error");
                return;
            }

            const webhookBtn = document.getElementById('amazonWebhookBtn');
            const loading = document.getElementById('loading');
            const webhookMessageSection = document.getElementById('webhookMessageSection');
            const webhookMessageContent = document.getElementById('webhookMessageContent');

            webhookBtn.disabled = true;
            loading.style.display = "block";
            webhookMessageContent.innerHTML = "";
            webhookMessageSection.style.display = "block";
            let totalProcessedCount = 0;

            for (let i = 0; i < amazonProductQueue.length; i++) {
                const produto = amazonProductQueue[i];
                loading.querySelector("p").textContent = `Processando Amazon ${i + 1} de ${amazonProductQueue.length}...`;

                try {
                    // 1. Processamento (Geração de Mensagem)
                    const response = await fetch('/webhook/processar', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            url_produto: produto.productUrl,
                            afiliado_link: produto.affiliateUrl
                        })
                    });

                    const data = await response.json();
                    if (!response.ok) throw new Error(data.error || 'Erro desconhecido no servidor.');
                    
                    totalProcessedCount++;
                    const message = data.final_message;
                    const imageUrl = data.image_url;

                    // Exibir a mensagem gerada
                    displayWebhookResponse(message, 'success', imageUrl, true);
                    
                    // ⭐ NOVO PASSO: Enviar a mensagem gerada via Baileys
                    loading.querySelector("p").textContent = `Enviando Amazon ${i + 1} de ${amazonProductQueue.length} para o WhatsApp...`;

                    const sendResult = await sendGeneratedMessage(message, imageUrl);

                    if (sendResult.success) {
                        console.log(`✅ Produto Amazon ${i + 1} enviado com sucesso via Baileys.`);
                    } else {
                        console.error(`❌ Produto Amazon ${i + 1} falhou no envio via Baileys: ${sendResult.error}`);
                        showAlert(`Falha no envio do produto Amazon ${i + 1} para o WhatsApp.`, "error");
                    }

                } catch (error) {
                    console.error("Erro ao processar produto da Amazon:", error);
                    displayWebhookResponse(`Erro ao processar ${produto.productUrl}: ${error.message}`, 'error', null, true);
                }
            }

            amazonProductQueue = [];
            atualizarFilaVisualAmazon();
            loading.style.display = "none";
            webhookBtn.disabled = false;
            showAlert(`Processamento da fila da Amazon concluído! ${totalProcessedCount} produtos processados.`, 'success');
        }
        
        if (amazonAddProductBtn) amazonAddProductBtn.addEventListener('click', adicionarProdutoFilaAmazon);
        if (amazonClearQueueBtn) amazonClearQueueBtn.addEventListener('click', limparFilaAmazon);
        if (amazonWebhookForm) amazonWebhookForm.addEventListener('submit', (e) => {
            e.preventDefault();
            processarFilaAmazon();
        });

        atualizarFilaVisualAmazon();
    }
  
  const filtroStatus = document.getElementById("filtroStatus");
  const filtroOrdem = document.getElementById("filtroOrdem");

  if (filtroStatus && filtroOrdem) {
    // Forçar refresh ao mudar filtros (invalidar cache)
    filtroStatus.addEventListener("change", () => {
      lastLoadTime = 0; // Invalidar cache
      loadAgendamentos(true);
    });
    filtroOrdem.addEventListener("change", () => {
      lastLoadTime = 0; // Invalidar cache
      loadAgendamentos(true);
    });
  }

  if (editarForm) {
      editarForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        const produtoId = document.getElementById('editarProdutoId').value;
        const imagemUrl = document.getElementById('editarImagemUrl').value.trim();
        const mensagem = document.getElementById('editarMensagem').value.trim();

        // Validação básica
        if (!produtoId) {
            showAlert('Erro: ID do produto não encontrado.', 'error');
            return;
        }

        const dadosParaAtualizar = {};

        // Só adiciona campos que não estão vazios
        if (imagemUrl) {
            dadosParaAtualizar.imagem_url = imagemUrl;
        }
        if (mensagem) {
            dadosParaAtualizar.final_message = mensagem;
        }

        // 🎟️ ADICIONAR DADOS DO CUPOM (se selecionado)
        const cupomId = document.getElementById('cupomId') ? document.getElementById('cupomId').value : '';
        const cupomTexto = document.getElementById('cupomTexto') ? document.getElementById('cupomTexto').value : '';

        if (cupomId && cupomTexto) {
            const cupomValor = document.getElementById('cupomValor').value;
            const cupomLimite = document.getElementById('cupomLimite').value;

            // Montar objeto cupom_info
            dadosParaAtualizar.cupom_info = JSON.stringify({
                cupom_id: cupomId,
                codigo: cupomTexto,
                porcentagem: parseFloat(cupomValor),
                limite_valor: parseFloat(cupomLimite)
            });

            // Calcular e adicionar preco_com_cupom
            if (produtoAtualData && produtoAtualData.preco_atual) {
                const extrairPreco = (precoStr) => {
                    if (!precoStr) return null;
                    // Passo 1: Remover "R$" e espaços
                    let numeroStr = precoStr.toString().replace(/R\$/g, '').replace(/\s/g, '');
                    // Passo 2: Remover pontos (separadores de milhar)
                    numeroStr = numeroStr.replace(/\./g, '');
                    // Passo 3: Trocar vírgula por ponto (separador decimal BR → US)
                    numeroStr = numeroStr.replace(/,/g, '.');
                    const numero = parseFloat(numeroStr);
                    return isNaN(numero) ? null : numero;
                };

                const precoBase = extrairPreco(produtoAtualData.preco_atual);
                if (precoBase) {
                    const porcentagem = parseFloat(cupomValor);
                    const limite = parseFloat(cupomLimite);
                    let desconto = precoBase * (porcentagem / 100);
                    if (desconto > limite) {
                        desconto = limite;
                    }
                    const valorFinal = precoBase - desconto;
                    dadosParaAtualizar.preco_com_cupom = `R$ ${valorFinal.toFixed(2).replace('.', ',')}`;
                    console.log(`💰 Cupom calculado: Preço base R$ ${precoBase.toFixed(2)} - Desconto R$ ${desconto.toFixed(2)} = Preço final ${dadosParaAtualizar.preco_com_cupom}`);
                }
            }
        }

        // Verifica se há pelo menos um campo para atualizar
        if (Object.keys(dadosParaAtualizar).length === 0) {
            showAlert('Por favor, preencha pelo menos um campo para atualizar.', 'error');
            return;
        }

        try {
            console.log('Enviando dados para atualização:', dadosParaAtualizar);
            
            const response = await fetch(`/produtos/${produtoId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dadosParaAtualizar)
            });

            const data = await response.json();
            console.log('Resposta do servidor:', data);

            if (response.ok) {
                showAlert('Produto atualizado com sucesso!', 'success');
                closeEditModal();
                loadAgendamentos(); 
            } else {
                throw new Error(data.error || 'Erro ao atualizar produto.');
            }
        } catch (error) {
            console.error('Erro ao editar produto:', error);
            showAlert(`Erro ao salvar alterações: ${error.message}`, 'error');
        }
    });
  }
  
  const agendamentoForm = document.getElementById('agendamentoForm');
  if (agendamentoForm) {
      agendamentoForm.addEventListener('submit', async function(e) {
          e.preventDefault();
          
          const produtoId = document.getElementById('agendarProdutoId').value;
          const data = document.getElementById('agendarData').value;
          const hora = document.getElementById('agendarHora').value;

          if (!data || !hora) {
              showAlert('Por favor, preencha a data e a hora.', 'error');
              return;
          }

          const agendamentoISO = `${data}T${hora}`;

          try {
              const response = await fetch(`/agendar_produto/${produtoId}`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ agendamento: agendamentoISO })
              });

              const result = await response.json();

              if (response.ok) {
                  showAlert('Produto agendado com sucesso!', 'success');
                  closeModal();
                  loadAgendamentos(); 
              } else {
                  throw new Error(result.error || 'Erro ao agendar produto.');
              }
          } catch (error) {
              showAlert(error.message, 'error');
          }
      });
  }
  
  // Adiciona funções que estavam faltando
  window.displayResults = function(resultados, total) {
    const resultsSection = document.getElementById("resultsSection");
    const productsGrid = document.getElementById("productsGrid");
    const resultsCount = document.getElementById("resultsCount");
    
    if (!resultsSection || !productsGrid || !resultsCount) {
      console.error('Elementos necessários não encontrados para displayResults');
      return;
    }
    
    resultsCount.textContent = `${total} produto${total !== 1 ? 's' : ''} encontrado${total !== 1 ? 's' : ''}`;
    
    productsGrid.innerHTML = '';
    
    if (resultados && resultados.length > 0) {
      resultados.forEach(produto => {
        const card = createProductCard(produto);
        productsGrid.appendChild(card);
      });
    } else {
      productsGrid.innerHTML = '<p>Nenhum produto encontrado.</p>';
    }
    
    resultsSection.style.display = "block";
    resultsSection.scrollIntoView({ behavior: "smooth" });
  };
  
  window.displayProdutoDetalhado = function(produto) {
    const produtoSection = document.getElementById("produtoSection");
    const produtoDetalhado = document.getElementById("produtoDetalhado");
    
    if (!produtoSection || !produtoDetalhado) {
      console.error('Elementos necessários não encontrados para displayProdutoDetalhado');
      return;
    }
    
    produtoDetalhado.innerHTML = '';
    const card = createProductCard(produto, true);
    produtoDetalhado.appendChild(card);
    
    produtoSection.style.display = "block";
    produtoSection.scrollIntoView({ behavior: "smooth" });
  };
  
  function createProductCard(produto, isDetailed = false) {
    const card = document.createElement("div");
    card.className = "product-card";
    
    const imageUrl = produto.imagem || produto.imagem_url || '';
    const title = produto.titulo || 'Título não disponível';
    const currentPrice = produto.preco_atual || 'Preço não disponível';
    const originalPrice = produto.preco_original || '';
    const discount = produto.desconto || '';
    const link = produto.link || produto.link_produto || '#';
    
    let priceHtml = `<div class="product-price-atual">${currentPrice}</div>`;
    
    if (originalPrice && originalPrice !== currentPrice) {
      priceHtml = `
        <div class="product-price-original">${originalPrice}</div>
        <div class="product-price-atual">${currentPrice}</div>
      `;
    }
    
    if (discount) {
      priceHtml += `<div class="product-discount">${discount}% OFF</div>`;
    }
    
    card.innerHTML = `
      <div class="product-header">
        ${imageUrl ? `<img src="${imageUrl}" alt="${title}" class="product-image" onerror="this.style.display='none'">` : ''}
        <div class="product-info">
          <div class="product-title">${title}</div>
          ${priceHtml}
        </div>
      </div>
      <div class="product-actions">
        <a href="${link}" target="_blank" class="btn-link">Ver Produto</a>
        ${isDetailed ? '' : `<button class="btn" onclick="enviarParaWebhook('${JSON.stringify(produto).replace(/'/g, "\\'")}')">Gerar Mensagem</button>`}
      </div>
    `;
    
    return card;
  }
  
  window.enviarParaWebhook = function(produtoJson) {
    try {
      const produto = JSON.parse(produtoJson);
      // Aqui, você pode implementar a chamada para `/processar_para_envio` com este produto
      console.log('Gerando mensagem para produto:', produto);
      showAlert('Funcionalidade de geração de mensagem será implementada em breve neste botão', 'info');
    } catch (error) {
      console.error('Erro ao processar produto para webhook:', error);
      showAlert('Erro ao processar produto', 'error');
    }
  };
  
  // Funções de configuração
  window.trocarBucketConfig = function() {
    const bucketSelector = document.getElementById('bucketSelector');
    const bucketAtualInfo = document.getElementById('bucketAtualInfo');
    
    if (bucketSelector && bucketAtualInfo) {
      const selectedBucket = bucketSelector.value;
      bucketAtualInfo.textContent = selectedBucket;
      localStorage.setItem('selected_bucket', selectedBucket);
      showAlert(`Bucket selecionado: ${selectedBucket}`, 'info');
    }
  };
  
  window.salvarConfiguracoes = function() {
    const supabaseUrl = document.getElementById('supabaseUrl');
    const bucketSelector = document.getElementById('bucketSelector');
    
    if (supabaseUrl && bucketSelector) {
      const url = supabaseUrl.value.trim();
      const bucket = bucketSelector.value;
      
      if (url) {
        localStorage.setItem('supabase_url', url);
      }
      localStorage.setItem('selected_bucket', bucket);
      
      showAlert('Configurações salvas com sucesso!', 'success');
      
      // Reinicializa o Supabase client se a URL mudou
      if (url) {
        initializeSupabase();
      }
    } else {
      showAlert('Erro ao salvar configurações', 'error');
    }
  };
  
  window.testarConexao = function() {
    const configStatus = document.getElementById('configStatus');
    
    if (!configStatus) return;
    
    configStatus.style.display = 'block';
    configStatus.style.backgroundColor = '#fff3cd';
    configStatus.style.borderColor = '#ffeaa7';
    configStatus.style.color = '#856404';
    configStatus.textContent = 'Testando conexão...';
    
    // Simula teste de conexão
    setTimeout(() => {
      if (supabaseInitialized) {
        configStatus.style.backgroundColor = '#d4edda';
        configStatus.style.borderColor = '#c3e6cb';
        configStatus.style.color = '#155724';
        configStatus.textContent = '✅ Conexão com Supabase bem-sucedida!';
        showAlert('Conexão testada com sucesso!', 'success');
      } else {
        configStatus.style.backgroundColor = '#f8d7da';
        configStatus.style.borderColor = '#f5c6cb';
        configStatus.style.color = '#721c24';
        configStatus.textContent = '❌ Erro na conexão com Supabase';
        showAlert('Erro na conexão. Verifique as configurações.', 'error');
      }
    }, 2000);
  };
  
  // Bucket atual
  let bucketAtual = localStorage.getItem('selected_bucket') || 'imagens_melhoradas_tech';
  
  // Funções do seletor de imagens
  window.abrirSeletorImagens = function() {
    const modal = document.getElementById('seletorImagensModal');
    if (modal) {
      modal.style.display = 'block';
      const bucketAtivo = document.getElementById('modalBucketAtivo');
      if (bucketAtivo) {
        bucketAtivo.textContent = bucketAtual;
      }
    }
  };
  
  window.fecharSeletorImagens = function() {
    const modal = document.getElementById('seletorImagensModal');
    if (modal) {
      modal.style.display = 'none';
    }
  };
  
  window.carregarImagens = function() {
    const loadingImagens = document.getElementById('loadingImagens');
    const imagensGrid = document.getElementById('imagensGrid');
    
    if (!loadingImagens || !imagensGrid) {
      showAlert('Elementos do modal não encontrados', 'error');
      return;
    }
    
    loadingImagens.style.display = 'block';
    imagensGrid.innerHTML = '';
    
    // Simula carregamento de imagens
    setTimeout(() => {
      loadingImagens.style.display = 'none';
      imagensGrid.innerHTML = `
        <p style="text-align: center; color: #666; margin: 40px;">
          🔧 Funcionalidade de carregamento de imagens será implementada em breve.<br>
          Por enquanto, cole o link da imagem diretamente no campo acima.
        </p>
      `;
      showAlert('Funcionalidade em desenvolvimento', 'info');
    }, 1000);
  };
  
  window.trocarBucket = function() {
    const bucketSelect = document.getElementById('bucketSelect');
    if (bucketSelect) {
      bucketAtual = bucketSelect.value;
      localStorage.setItem('selected_bucket', bucketAtual);
      showAlert(`Bucket alterado para: ${bucketAtual}`, 'info');
      carregarImagens();
    }
  };
  
  window.buscarImagens = function() {
    const searchImagens = document.getElementById('searchImagens');
    if (searchImagens) {
      const termo = searchImagens.value.trim();
      showAlert(termo ? `Buscando por: ${termo}` : 'Carregando todas as imagens', 'info');
      carregarImagens();
    }
  };
  
  window.paginaAnterior = function() {
    showAlert('Página anterior - funcionalidade em desenvolvimento', 'info');
  };
  
  window.proximaPagina = function() {
    showAlert('Próxima página - funcionalidade em desenvolvimento', 'info');
  };

  // 🔥 LISTENER PARA ATUALIZAÇÃO AUTOMÁTICA QUANDO PRODUTO FOR APROVADO
  window.addEventListener('message', (event) => {
    // Verificar se é uma mensagem de aprovação de produto
    if (event.data && event.data.type === 'PRODUTO_APROVADO') {
      console.log('✅ Produto aprovado detectado! Atualizando lista...', event.data);

      // Se estiver na aba de agendamento, atualizar imediatamente
      const agendamentoTab = document.getElementById('agendamento');
      if (agendamentoTab && agendamentoTab.style.display !== 'none') {
        console.log('🔄 Atualizando lista de agendamentos...');
        loadAgendamentos(true); // Forçar refresh do servidor
        showAlert('✅ Novo produto aprovado adicionado à lista!', 'success');
      } else {
        console.log('ℹ️ Aguardando usuário abrir aba de agendamento');
        // Marcar que há atualização pendente
        window.pendingProductUpdate = true;
      }
    }
  });

  // 🔥 AUTO-REFRESH QUANDO ABRIR A ABA DE AGENDAMENTO
  const originalOpenTab = window.openTab;
  window.openTab = function(evt, tabName) {
    originalOpenTab(evt, tabName);

    // Se abriu a aba de agendamento e há atualização pendente
    if (tabName === 'agendamento') {
      if (window.pendingProductUpdate) {
        console.log('🔄 Atualizando lista com produtos pendentes...');
        loadAgendamentos(true); // Forçar refresh do servidor
        showAlert('✅ Lista atualizada com novos produtos!', 'success');
        window.pendingProductUpdate = false;
      }
    }
  };

  // 🔥 AUTO-REFRESH PERIÓDICO NA ABA DE AGENDAMENTO (A CADA 15 SEGUNDOS)
  setInterval(() => {
    const agendamentoTab = document.getElementById('agendamento');
    if (agendamentoTab && agendamentoTab.style.display !== 'none') {
      console.log('🔄 Auto-refresh: Atualizando lista de agendamentos...');
      loadAgendamentos(true); // Forçar refresh do servidor
    }
  }, 15000); // 15 segundos (mais frequente)

  // 🔥 CONFIGURAR ÁREA DE PASTE DE IMAGEM
  setupImagePasteArea();
});

// ==================== FUNÇÕES PARA COPIAR E COLAR IMAGENS ====================

let currentPastedImage = null; // Armazena a imagem colada

function setupImagePasteArea() {
  const pasteZone = document.getElementById('imagePasteZone');
  if (!pasteZone) return;

  // Listener para paste em qualquer lugar do modal quando aberto
  document.addEventListener('paste', handlePasteEvent);

  // Efeito visual ao passar mouse
  pasteZone.addEventListener('mouseenter', function() {
    this.style.borderColor = '#764ba2';
    this.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    this.style.transform = 'scale(1.02)';
    const texts = this.querySelectorAll('div');
    texts.forEach(t => t.style.color = 'white');
  });

  pasteZone.addEventListener('mouseleave', function() {
    this.style.borderColor = '#667eea';
    this.style.background = 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)';
    this.style.transform = 'scale(1)';
    const texts = this.querySelectorAll('div');
    texts[1].style.color = '#667eea';
    texts[2].style.color = '#666';
  });
}

function focusOnPasteArea() {
  showAlert('✨ Área ativa! Use Ctrl+V para colar uma imagem', 'info');
}

async function handlePasteEvent(e) {
  // Verificar se o modal de edição está aberto
  const modal = document.getElementById('editarModal');
  if (!modal || modal.style.display !== 'block') return;

  const items = e.clipboardData?.items;
  if (!items) return;

  for (let i = 0; i < items.length; i++) {
    const item = items[i];

    // Verificar se é uma imagem
    if (item.type.indexOf('image') !== -1) {
      e.preventDefault();

      const file = item.getAsFile();
      console.log('📋 Imagem colada:', file.name, file.type, file.size);

      showAlert('📸 Imagem detectada! Processando...', 'info');

      await processImageFile(file);
      break;
    }
  }
}

function handleFileSelect(event) {
  const file = event.target.files[0];
  if (!file) return;

  if (!file.type.startsWith('image/')) {
    showAlert('❌ Por favor, selecione um arquivo de imagem', 'error');
    return;
  }

  console.log('📁 Arquivo selecionado:', file.name, file.type, file.size);
  showAlert('📸 Imagem selecionada! Processando...', 'info');

  processImageFile(file);
}

async function processImageFile(file) {
  try {
    // Mostrar preview imediato
    const reader = new FileReader();

    reader.onload = async function(e) {
      const base64Image = e.target.result;
      currentPastedImage = base64Image;

      // Atualizar preview
      const preview = document.getElementById('imagePreview');
      const placeholder = document.getElementById('imagePreviewPlaceholder');

      if (preview && placeholder) {
        preview.src = base64Image;
        preview.style.display = 'block';
        placeholder.style.display = 'none';
      }

      // Atualizar visual da paste zone
      updatePasteZoneWithImage(file.name);

      // Fazer upload para Supabase automaticamente
      showAlert('⬆️ Fazendo upload da imagem...', 'info');

      const uploadedUrl = await uploadImageToSupabase(base64Image, file.name);

      if (uploadedUrl) {
        // Atualizar campo de URL
        const urlInput = document.getElementById('editarImagemUrl');
        if (urlInput) {
          urlInput.value = uploadedUrl;
        }

        showAlert('✅ Imagem enviada com sucesso para o Supabase!', 'success');
        console.log('✅ URL da imagem:', uploadedUrl);
      } else {
        showAlert('⚠️ Imagem carregada mas não foi enviada ao Supabase', 'warning');
      }
    };

    reader.onerror = function(error) {
      console.error('Erro ao ler arquivo:', error);
      showAlert('❌ Erro ao processar imagem', 'error');
    };

    reader.readAsDataURL(file);

  } catch (error) {
    console.error('Erro ao processar imagem:', error);
    showAlert('❌ Erro ao processar imagem: ' + error.message, 'error');
  }
}

function updatePasteZoneWithImage(fileName) {
  const pasteZone = document.getElementById('imagePasteZone');
  if (!pasteZone) return;

  pasteZone.innerHTML = `
    <div style="font-size: 48px; margin-bottom: 10px;">✅</div>
    <div style="font-weight: 600; color: #10b981; font-size: 16px; margin-bottom: 5px;">
      Imagem carregada!
    </div>
    <div style="color: #666; font-size: 13px; margin-bottom: 10px;">
      ${fileName}
    </div>
    <button
      type="button"
      onclick="resetPasteZone()"
      style="
        padding: 8px 16px;
        background: #ef4444;
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-size: 13px;
        font-weight: 500;
      "
    >
      🗑️ Remover
    </button>
  `;

  pasteZone.style.background = 'linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)';
  pasteZone.style.borderColor = '#10b981';
}

function resetPasteZone() {
  const pasteZone = document.getElementById('imagePasteZone');
  if (!pasteZone) return;

  pasteZone.innerHTML = `
    <div style="font-size: 48px; margin-bottom: 10px;">📋</div>
    <div style="font-weight: 600; color: #667eea; font-size: 16px; margin-bottom: 5px;">
      Cole uma imagem aqui
    </div>
    <div style="color: #666; font-size: 13px;">
      Copie uma imagem (Ctrl+C) e clique aqui para colar (Ctrl+V)
    </div>
    <input
      type="file"
      id="imageFileInput"
      accept="image/*"
      style="display: none;"
      onchange="handleFileSelect(event)"
    />
    <button
      type="button"
      onclick="event.stopPropagation(); document.getElementById('imageFileInput').click();"
      style="
        margin-top: 15px;
        padding: 8px 16px;
        background: #667eea;
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-size: 13px;
        font-weight: 500;
      "
    >
      📁 Ou escolher arquivo
    </button>
  `;

  pasteZone.style.background = 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)';
  pasteZone.style.borderColor = '#667eea';
  pasteZone.onclick = focusOnPasteArea;

  currentPastedImage = null;

  // Limpar preview
  const preview = document.getElementById('imagePreview');
  const placeholder = document.getElementById('imagePreviewPlaceholder');
  if (preview && placeholder) {
    preview.style.display = 'none';
    placeholder.style.display = 'block';
  }

  // Limpar campo de URL
  const urlInput = document.getElementById('editarImagemUrl');
  if (urlInput) {
    urlInput.value = '';
  }

  showAlert('🗑️ Imagem removida', 'info');
}

async function uploadImageToSupabase(base64Image, fileName) {
  try {
    // Fazer upload via endpoint do Flask
    const response = await fetch('/upload-image', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        image: base64Image,
        filename: fileName || 'pasted-image.png'
      })
    });

    const result = await response.json();

    if (result.success && result.url) {
      console.log('✅ Upload para Supabase concluído:', result.url);
      return result.url;
    } else {
      console.error('❌ Erro no upload:', result.error);
      return null;
    }
  } catch (error) {
    console.error('❌ Erro ao fazer upload:', error);
    return null;
  }
}

// ============================================
// SISTEMA DE ENVIO DE MENSAGENS PARA GRUPOS
// ============================================

let produtoAtualEnvio = null;
let gruposDisponiveis = [];
let gruposSelecionados = new Set();

/**
 * Abre o modal de envio para um produto específico
 */
async function abrirModalEnvio(produtoId) {
  try {
    console.log('📤 Abrindo modal de envio para produto:', produtoId);

    // Verificar se elementos do modal existem
    const modal = document.getElementById('modalEnviarGrupos');
    const tituloEl = document.getElementById('produtoTituloEnvio');
    const precoEl = document.getElementById('produtoPrecoEnvio');

    if (!modal) {
      console.error('❌ Modal não encontrado no DOM');
      alert('❌ Erro: Modal de envio não foi carregado. Recarregue a página.');
      return;
    }

    if (!tituloEl || !precoEl) {
      console.error('❌ Elementos do produto não encontrados:', { tituloEl, precoEl });
      alert('❌ Erro: Elementos do modal não foram carregados. Recarregue a página.');
      return;
    }

    // Buscar informações do produto
    const response = await fetch(`/produtos/${produtoId}`);
    const data = await response.json();

    if (!data.success) {
      alert('❌ Erro ao carregar produto: ' + (data.error || 'Desconhecido'));
      return;
    }

    produtoAtualEnvio = data.produto;
    console.log('✅ Produto carregado:', produtoAtualEnvio);

    // Preencher informações do produto
    tituloEl.textContent = produtoAtualEnvio.titulo || produtoAtualEnvio.link_produto || 'Sem título';
    precoEl.textContent = produtoAtualEnvio.preco_atual || produtoAtualEnvio.preco_com_cupom || 'Preço não disponível';

    // Carregar grupos
    await carregarGruposWhatsApp();

    // Mostrar modal
    modal.style.display = 'flex';

  } catch (error) {
    console.error('❌ Erro ao abrir modal:', error);
    alert('❌ Erro ao abrir modal de envio: ' + error.message);
  }
}

/**
 * Fecha o modal de envio
 */
function fecharModalEnvio() {
  document.getElementById('modalEnviarGrupos').style.display = 'none';
  gruposSelecionados.clear();
  produtoAtualEnvio = null;
  console.log('✅ Modal fechado');
}

/**
 * Carrega lista de grupos do WhatsApp
 */
async function carregarGruposWhatsApp() {
  const listaGrupos = document.getElementById('listaGruposEnvio');
  listaGrupos.innerHTML = '<p style="text-align: center; color: #999; padding: 20px;">🔄 Carregando grupos...</p>';

  try {
    console.log('📡 Buscando grupos do WhatsApp e grupos fixos...');

    // Buscar grupos do WhatsApp e grupos fixos em paralelo
    const [gruposResponse, gruposFixosResponse] = await Promise.all([
      fetch('/whatsapp/groups'),
      fetch('/grupos-fixos')
    ]);

    const data = await gruposResponse.json();
    const gruposFixosData = await gruposFixosResponse.json();

    console.log('📱 Resposta dos grupos:', data);
    console.log('📌 Grupos fixos:', gruposFixosData);

    if (data.error) {
      throw new Error(data.error);
    }

    if (!data.groups || data.groups.length === 0) {
      listaGrupos.innerHTML = `
        <div style="text-align: center; padding: 30px; color: #999;">
          <div style="font-size: 48px; margin-bottom: 15px;">📭</div>
          <p style="font-size: 16px; margin-bottom: 10px;">Nenhum grupo encontrado</p>
          <p style="font-size: 13px; color: #666;">Verifique se o WhatsApp está conectado</p>
          <button onclick="window.location.href='/whatsapp-monitor'" class="btn btn-primary" style="margin-top: 15px;">
            📱 Ir para WhatsApp Monitor
          </button>
        </div>
      `;
      return;
    }

    gruposDisponiveis = data.groups;

    // Criar set com IDs dos grupos fixos ativos
    const gruposFixosAtivos = new Set(
      (gruposFixosData.grupos || [])
        .filter(g => g.ativo)
        .map(g => g.grupo_id)
    );

    console.log(`✅ ${gruposDisponiveis.length} grupos carregados, ${gruposFixosAtivos.size} grupos fixos ativos`);

    // Renderizar lista de grupos
    listaGrupos.innerHTML = '';

    data.groups.forEach((grupo, index) => {
      const isGrupoFixo = gruposFixosAtivos.has(grupo.id);

      const grupoDiv = document.createElement('div');
      grupoDiv.className = 'grupo-item-envio';
      grupoDiv.onclick = (e) => {
        if (e.target.tagName !== 'INPUT') {
          toggleGrupo(grupo.id);
        }
      };

      grupoDiv.innerHTML = `
        <input
          type="checkbox"
          id="grupo-${grupo.id}"
          ${isGrupoFixo ? 'checked' : ''}
          onchange="toggleGrupo('${grupo.id}')"
          onclick="event.stopPropagation()"
        />
        <div class="grupo-info-envio">
          <div class="grupo-nome-envio">
            ${grupo.name}
            ${grupo.monitored ? '<span class="grupo-monitorado-badge">Monitorado</span>' : ''}
            ${isGrupoFixo ? '<span class="grupo-fixo-badge">📌 Grupo Fixo</span>' : ''}
          </div>
          <div class="grupo-participantes-envio">
            👥 ${grupo.participants} participantes
          </div>
        </div>
      `;

      listaGrupos.appendChild(grupoDiv);

      // Se for grupo fixo, adicionar aos selecionados
      if (isGrupoFixo) {
        gruposSelecionados.add(grupo.id);
      }
    });

  } catch (error) {
    console.error('❌ Erro ao carregar grupos:', error);
    listaGrupos.innerHTML = `
      <div style="text-align: center; padding: 30px; color: #f44336;">
        <div style="font-size: 48px; margin-bottom: 15px;">❌</div>
        <p style="font-size: 16px; margin-bottom: 10px;">Erro ao carregar grupos</p>
        <p style="font-size: 13px; color: #666; margin-bottom: 15px;">${error.message}</p>
        <button onclick="carregarGruposWhatsApp()" class="btn btn-primary">
          🔄 Tentar Novamente
        </button>
      </div>
    `;
  }
}

/**
 * Toggle seleção de grupo
 */
function toggleGrupo(grupoId) {
  const checkbox = document.getElementById(`grupo-${grupoId}`);

  if (gruposSelecionados.has(grupoId)) {
    gruposSelecionados.delete(grupoId);
    checkbox.checked = false;
    console.log('➖ Grupo desmarcado:', grupoId);
  } else {
    gruposSelecionados.add(grupoId);
    checkbox.checked = true;
    console.log('✅ Grupo selecionado:', grupoId);
  }

  atualizarResumoSelecao();
}

/**
 * Atualiza resumo de grupos selecionados
 */
function atualizarResumoSelecao() {
  const total = gruposSelecionados.size;
  const resumo = document.getElementById('resumoSelecaoEnvio');
  const totalSpan = document.getElementById('totalGruposSelecionados');

  if (!resumo || !totalSpan) {
    console.warn('⚠️ Elementos de resumo não encontrados');
    return;
  }

  totalSpan.textContent = total;

  if (total > 0) {
    resumo.style.display = 'block';
  } else {
    resumo.style.display = 'none';
  }
}

/**
 * Envia mensagem para grupos selecionados
 */
async function enviarParaGruposSelecionados() {
  if (gruposSelecionados.size === 0) {
    alert('⚠️ Selecione pelo menos um grupo');
    return;
  }

  if (!produtoAtualEnvio) {
    alert('❌ Produto não encontrado');
    return;
  }

  // Confirmar envio
  const produtoNome = produtoAtualEnvio.titulo || produtoAtualEnvio.link_produto || 'Produto';
  const confirmar = confirm(
    `📤 Enviar mensagem para ${gruposSelecionados.size} grupo(s)?\n\n` +
    `Produto: ${produtoNome.substring(0, 60)}${produtoNome.length > 60 ? '...' : ''}`
  );

  if (!confirmar) return;

  const btnEnviar = document.getElementById('btnEnviarMensagem');
  const textoOriginal = btnEnviar.innerHTML;
  btnEnviar.disabled = true;
  btnEnviar.innerHTML = '⏳ Enviando...';

  try {
    console.log('📤 Enviando mensagem...');
    console.log('  Produto ID:', produtoAtualEnvio.id);
    console.log('  Grupos:', Array.from(gruposSelecionados));

    const response = await fetch('/enviar-mensagem', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        produto_id: produtoAtualEnvio.id,
        grupos: Array.from(gruposSelecionados)
      })
    });

    const result = await response.json();
    console.log('📨 Resultado do envio:', result);

    if (result.success) {
      alert(
        `✅ ${result.message}\n\n` +
        `Enviado com sucesso: ${result.detalhes.total_enviado}\n` +
        `Falhas: ${result.detalhes.total_falhou}`
      );

      fecharModalEnvio();

      // Atualizar lista de produtos se estiver na aba de agendamento
      if (typeof listarProdutosAgendados === 'function') {
        listarProdutosAgendados();
      }
    } else {
      alert(`❌ Erro ao enviar: ${result.error}`);
    }

  } catch (error) {
    console.error('❌ Erro ao enviar mensagem:', error);
    alert(`❌ Erro ao enviar mensagem: ${error.message}`);
  } finally {
    btnEnviar.disabled = false;
    btnEnviar.innerHTML = textoOriginal;
  }
}

console.log('✅ Sistema de envio de mensagens carregado');

// ============================================================================
// SISTEMA DE GRUPOS FIXOS PARA AGENDAMENTO AUTOMÁTICO
// ============================================================================

/**
 * Carrega e exibe a lista de grupos fixos
 */
async function carregarGruposFixos() {
  console.log('📋 Carregando grupos fixos...');
  const container = document.getElementById('listaGruposFixos');

  if (!container) {
    console.warn('⚠️ Container de grupos fixos não encontrado');
    return;
  }

  container.innerHTML = '<p style="text-align: center; color: #999;">Carregando grupos fixos...</p>';

  try {
    const response = await fetch('/grupos-fixos');
    const result = await response.json();

    if (!result.success) {
      throw new Error(result.error || 'Erro ao carregar grupos fixos');
    }

    const grupos = result.grupos || [];

    if (grupos.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 30px; color: #999;">
          <div style="font-size: 48px; margin-bottom: 10px;">📱</div>
          <p style="margin: 0; font-size: 14px;">Nenhum grupo fixo configurado</p>
          <small>Adicione grupos para receber mensagens agendadas automaticamente</small>
        </div>
      `;
      return;
    }

    // Renderiza a lista de grupos
    container.innerHTML = grupos.map(grupo => `
      <div class="grupo-fixo-item" style="
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 15px;
        border: 1px solid #e1e8ed;
        border-radius: 8px;
        margin-bottom: 10px;
        background: white;
        transition: all 0.2s;
      " onmouseover="this.style.borderColor='#667eea'" onmouseout="this.style.borderColor='#e1e8ed'">
        <div style="flex: 1;">
          <div style="font-weight: 600; color: #333; margin-bottom: 5px;">
            📱 ${grupo.grupo_nome}
          </div>
          <div style="font-size: 12px; color: #666; font-family: monospace;">
            ID: ${grupo.grupo_id}
          </div>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
          <label class="switch" style="position: relative; display: inline-block; width: 50px; height: 24px;">
            <input
              type="checkbox"
              ${grupo.ativo ? 'checked' : ''}
              onchange="alternarStatusGrupoFixo('${grupo.grupo_id}', this.checked)"
              style="opacity: 0; width: 0; height: 0;"
            >
            <span style="
              position: absolute;
              cursor: pointer;
              top: 0;
              left: 0;
              right: 0;
              bottom: 0;
              background-color: ${grupo.ativo ? '#4CAF50' : '#ccc'};
              transition: .4s;
              border-radius: 24px;
            ">
              <span style="
                position: absolute;
                content: '';
                height: 18px;
                width: 18px;
                left: ${grupo.ativo ? '26px' : '3px'};
                bottom: 3px;
                background-color: white;
                transition: .4s;
                border-radius: 50%;
                display: block;
              "></span>
            </span>
          </label>
          <button
            onclick="confirmarRemoverGrupoFixo('${grupo.grupo_id}', '${grupo.grupo_nome.replace(/'/g, "\\'")}')"
            style="
              background-color: #e74c3c;
              color: white;
              border: none;
              padding: 8px 12px;
              border-radius: 6px;
              cursor: pointer;
              font-size: 12px;
              font-weight: 600;
              transition: all 0.2s;
            "
            onmouseover="this.style.backgroundColor='#c0392b'"
            onmouseout="this.style.backgroundColor='#e74c3c'"
          >
            🗑️ Remover
          </button>
        </div>
      </div>
    `).join('');

    console.log(`✅ ${grupos.length} grupos fixos carregados`);

  } catch (error) {
    console.error('❌ Erro ao carregar grupos fixos:', error);
    container.innerHTML = `
      <div style="text-align: center; padding: 20px; color: #e74c3c;">
        <p>❌ Erro ao carregar grupos fixos</p>
        <small>${error.message}</small>
      </div>
    `;
    showAlert('Erro ao carregar grupos fixos: ' + error.message, 'error');
  }
}

/**
 * Abre modal para adicionar grupo fixo
 */
function abrirModalAdicionarGrupoFixo() {
  const modal = document.getElementById('modalAdicionarGrupoFixo');
  if (modal) {
    modal.style.display = 'block';
  }
}

/**
 * Fecha modal de adicionar grupo fixo
 */
function fecharModalAdicionarGrupoFixo() {
  const modal = document.getElementById('modalAdicionarGrupoFixo');
  if (modal) {
    modal.style.display = 'none';
  }

  // Limpa a lista de grupos disponíveis
  const lista = document.getElementById('listaGruposDisponiveis');
  if (lista) {
    lista.innerHTML = `
      <p style="text-align: center; color: #999; padding: 20px;">
        Clique em "Carregar Grupos WhatsApp" para listar os grupos disponíveis
      </p>
    `;
  }
}

/**
 * Carrega lista de grupos WhatsApp disponíveis
 */
async function carregarGruposDisponiveis() {
  console.log('📱 Carregando grupos WhatsApp disponíveis...');

  const lista = document.getElementById('listaGruposDisponiveis');
  const loading = document.getElementById('loadingGruposDisponiveis');

  if (!lista || !loading) {
    console.warn('⚠️ Elementos não encontrados');
    return;
  }

  loading.style.display = 'block';
  lista.innerHTML = '';

  try {
    const response = await fetch('/whatsapp/groups');
    const result = await response.json();

    loading.style.display = 'none';

    // A API do WhatsApp retorna diretamente {"groups": [...]}
    const grupos = result.groups || [];

    if (grupos.length === 0) {
      lista.innerHTML = `
        <p style="text-align: center; color: #999; padding: 20px;">
          Nenhum grupo WhatsApp encontrado
        </p>
      `;
      return;
    }

    // Renderiza a lista de grupos disponíveis
    lista.innerHTML = grupos.map(grupo => `
      <div style="
        padding: 15px;
        border: 1px solid #e1e8ed;
        border-radius: 8px;
        margin-bottom: 10px;
        background: white;
        cursor: pointer;
        transition: all 0.2s;
      " onclick="adicionarGrupoFixoSelecionado('${grupo.id}', '${(grupo.name || grupo.subject || 'Sem nome').replace(/'/g, "\\'")}')">
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <div style="flex: 1;">
            <div style="font-weight: 600; color: #333; margin-bottom: 5px;">
              ${grupo.name || grupo.subject || 'Sem nome'}
            </div>
            <div style="font-size: 12px; color: #666;">
              ${grupo.size || grupo.participants?.length || 0} participantes
            </div>
          </div>
          <button
            onclick="event.stopPropagation(); adicionarGrupoFixoSelecionado('${grupo.id}', '${(grupo.name || grupo.subject || 'Sem nome').replace(/'/g, "\\'")}')"
            style="
              background-color: #667eea;
              color: white;
              border: none;
              padding: 8px 16px;
              border-radius: 6px;
              cursor: pointer;
              font-size: 12px;
              font-weight: 600;
            "
          >
            ➕ Adicionar
          </button>
        </div>
      </div>
    `).join('');

    console.log(`✅ ${grupos.length} grupos WhatsApp carregados`);

  } catch (error) {
    console.error('❌ Erro ao carregar grupos WhatsApp:', error);
    loading.style.display = 'none';
    lista.innerHTML = `
      <div style="text-align: center; padding: 20px; color: #e74c3c;">
        <p>❌ Erro ao carregar grupos WhatsApp</p>
        <small>${error.message}</small>
        <br><br>
        <small>Certifique-se de que o WhatsApp Monitor está conectado</small>
      </div>
    `;
    showAlert('Erro ao carregar grupos: ' + error.message, 'error');
  }
}

/**
 * Adiciona um grupo selecionado à lista de grupos fixos
 */
async function adicionarGrupoFixoSelecionado(grupoId, grupoNome) {
  console.log(`➕ Adicionando grupo fixo: ${grupoNome} (${grupoId})`);

  try {
    const response = await fetch('/grupos-fixos', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        grupo_id: grupoId,
        grupo_nome: grupoNome
      })
    });

    const result = await response.json();

    if (!result.success) {
      throw new Error(result.error || 'Erro ao adicionar grupo fixo');
    }

    showAlert(`✅ Grupo "${grupoNome}" adicionado com sucesso!`, 'success');

    // Fecha o modal
    fecharModalAdicionarGrupoFixo();

    // Recarrega a lista de grupos fixos
    await carregarGruposFixos();

  } catch (error) {
    console.error('❌ Erro ao adicionar grupo fixo:', error);
    showAlert('Erro ao adicionar grupo: ' + error.message, 'error');
  }
}

/**
 * Alterna o status ativo/inativo de um grupo fixo
 */
async function alternarStatusGrupoFixo(grupoId, ativo) {
  console.log(`🔄 Alternando status do grupo ${grupoId} para ${ativo ? 'ativo' : 'inativo'}`);

  try {
    const response = await fetch(`/grupos-fixos/${grupoId}/toggle`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ ativo })
    });

    const result = await response.json();

    if (!result.success) {
      throw new Error(result.error || 'Erro ao alternar status');
    }

    showAlert(
      `✅ Grupo ${ativo ? 'ativado' : 'desativado'} com sucesso!`,
      'success'
    );

  } catch (error) {
    console.error('❌ Erro ao alternar status:', error);
    showAlert('Erro ao alternar status: ' + error.message, 'error');
    // Recarrega para reverter o switch
    await carregarGruposFixos();
  }
}

/**
 * Confirma e remove um grupo fixo
 */
function confirmarRemoverGrupoFixo(grupoId, grupoNome) {
  const confirmar = confirm(
    `❌ Deseja realmente remover o grupo "${grupoNome}" da lista de grupos fixos?\n\n` +
    'Ele não receberá mais as mensagens agendadas automaticamente.'
  );

  if (confirmar) {
    removerGrupoFixo(grupoId);
  }
}

/**
 * Remove um grupo fixo
 */
async function removerGrupoFixo(grupoId) {
  console.log(`🗑️ Removendo grupo fixo: ${grupoId}`);

  try {
    const response = await fetch(`/grupos-fixos/${grupoId}`, {
      method: 'DELETE'
    });

    const result = await response.json();

    if (!result.success) {
      throw new Error(result.error || 'Erro ao remover grupo fixo');
    }

    showAlert('✅ Grupo removido com sucesso!', 'success');

    // Recarrega a lista de grupos fixos
    await carregarGruposFixos();

  } catch (error) {
    console.error('❌ Erro ao remover grupo fixo:', error);
    showAlert('Erro ao remover grupo: ' + error.message, 'error');
  }
}

// Carrega grupos fixos quando a aba de configurações for aberta
document.addEventListener('DOMContentLoaded', () => {
  // Observer para detectar quando a aba de configurações é aberta
  const configTab = document.getElementById('tab-config');
  if (configTab) {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.target.classList.contains('active')) {
          carregarGruposFixos();
        }
      });
    });

    observer.observe(configTab, {
      attributes: true,
      attributeFilter: ['class']
    });
  }
});

console.log('✅ Sistema de grupos fixos carregado');

// ============================================================================
// SISTEMA DE CUPONS
// ============================================================================

let cuponsDisponiveis = [];

/**
 * Carrega cupons ativos do servidor
 */
async function carregarCuponsAtivos() {
  try {
    const response = await fetch('/cupons/ativos');
    const data = await response.json();

    if (data.success) {
      cuponsDisponiveis = data.cupons;
      preencherSelectCupons();
      console.log(`✅ ${cuponsDisponiveis.length} cupons ativos carregados`);
    }
  } catch (error) {
    console.error('Erro ao carregar cupons:', error);
  }
}

/**
 * Preenche o select de cupons com os cupons disponíveis
 */
function preencherSelectCupons() {
  const select = document.getElementById('cupomSelect');
  if (!select) return;

  // Limpa opções existentes (mantém apenas a primeira)
  while (select.options.length > 1) {
    select.remove(1);
  }

  // Adiciona cupons
  cuponsDisponiveis.forEach(cupom => {
    const option = document.createElement('option');
    option.value = cupom.id;
    option.textContent = `${cupom.codigo} - ${cupom.porcentagem}% (máx R$ ${cupom.limite_valor.toFixed(2)})`;
    option.dataset.codigo = cupom.codigo;
    option.dataset.porcentagem = cupom.porcentagem;
    option.dataset.limite = cupom.limite_valor;
    select.appendChild(option);
  });
}

/**
 * Quando seleciona um cupom no dropdown
 */
function selecionarCupom() {
  const select = document.getElementById('cupomSelect');
  const selectedOption = select.options[select.selectedIndex];

  if (!select.value) {
    // Nenhum cupom selecionado - limpar campos
    document.getElementById('cupomTexto').value = '';
    document.getElementById('cupomValor').value = '';
    document.getElementById('cupomLimite').value = '';
    document.getElementById('cupomId').value = '';
    document.getElementById('cupomTipo').value = 'porcentagem';
    atualizarPreviewComCupom(null);
    return;
  }

  // Preencher campos hidden com dados do cupom
  const cupomId = select.value;
  const codigo = selectedOption.dataset.codigo;
  const porcentagem = selectedOption.dataset.porcentagem;
  const limite = selectedOption.dataset.limite;

  document.getElementById('cupomTexto').value = codigo;
  document.getElementById('cupomValor').value = porcentagem;
  document.getElementById('cupomLimite').value = limite;
  document.getElementById('cupomId').value = cupomId;
  document.getElementById('cupomTipo').value = 'porcentagem';

  console.log(`✅ Cupom selecionado: ${codigo} (${porcentagem}% - máx R$ ${limite})`);

  // Calcular e atualizar preview
  calcularEAtualizarPreviewCupom();
}

/**
 * Calcula o desconto e atualiza o preview da mensagem
 */
function calcularEAtualizarPreviewCupom() {
  const cupomId = document.getElementById('cupomId').value;

  if (!cupomId || !produtoAtualData) {
    atualizarPreviewComCupom(null);
    return;
  }

  // Função para extrair número de string de preço brasileiro
  // Exemplos: "R$ 2.899,00" -> 2899.00 | "R$ 245,65" -> 245.65
  const extrairPreco = (precoStr) => {
    if (!precoStr) return null;

    console.log(`📊 [ANTES] Valor original: "${precoStr}"`);

    // Converter para string
    let numeroStr = String(precoStr);

    // Passo 1: Remover "R$" e espaços
    numeroStr = numeroStr.replace(/R\$/g, '').replace(/\s/g, '');
    console.log(`📊 [1] Após remover R$: "${numeroStr}"`);

    // Passo 2: Remover pontos (separadores de milhar)
    numeroStr = numeroStr.replace(/\./g, '');
    console.log(`📊 [2] Após remover pontos: "${numeroStr}"`);

    // Passo 3: Trocar vírgula por ponto (separador decimal BR → US)
    numeroStr = numeroStr.replace(/,/g, '.');
    console.log(`📊 [3] Após trocar vírgula: "${numeroStr}"`);

    // Passo 4: Converter para número
    const numero = parseFloat(numeroStr);
    console.log(`📊 [FINAL] Número convertido: ${numero}`);

    return isNaN(numero) ? null : numero;
  };

  // Usar preco_atual como base (preço de promoção atual)
  // Se houver preco_original, usar ele como "De" e preco_atual como base para cálculo
  const precoAtual = extrairPreco(produtoAtualData.preco_atual);
  const precoOriginal = extrairPreco(produtoAtualData.preco_original);

  // Definir qual preço usar como base para o cálculo do cupom
  const precoBase = precoAtual;

  // Definir qual preço mostrar como "original" no preview
  const precoParaMostrar = precoOriginal || precoAtual;

  if (!precoBase) {
    console.error('❌ Não foi possível extrair preço');
    atualizarPreviewComCupom(null);
    return;
  }

  const porcentagem = parseFloat(document.getElementById('cupomValor').value);
  const limite = parseFloat(document.getElementById('cupomLimite').value);
  const codigo = document.getElementById('cupomTexto').value;

  console.log('🔍 DEBUG COMPLETO - produtoAtualData:', produtoAtualData);
  console.log('💰 Calculando cupom:', {
    preco_atual_str: produtoAtualData.preco_atual,
    preco_original_str: produtoAtualData.preco_original,
    preco_atual_numero: precoAtual,
    preco_original_numero: precoOriginal,
    preco_base_numero: precoBase,
    preco_para_mostrar: precoParaMostrar,
    porcentagem,
    limite
  });

  // Calcular desconto
  let desconto = precoBase * (porcentagem / 100);
  if (desconto > limite) {
    desconto = limite;
  }

  const valorFinal = precoBase - desconto;

  atualizarPreviewComCupom({
    codigo,
    precoOriginal: precoParaMostrar, // Mostrar o preço original do produto no preview
    precoAtual: precoBase, // Preço atual usado para cálculo
    desconto,
    valorFinal,
    porcentagem,
    limite
  });
}

/**
 * Atualiza o preview da mensagem com cupom
 */
function atualizarPreviewComCupom(cupomData) {
  const previewElement = document.getElementById('cupomPreview');
  if (!previewElement) return;

  if (!cupomData) {
    previewElement.style.display = 'none';
    previewElement.innerHTML = '';

    // 🔄 RESTAURAR MENSAGEM ORIGINAL (sem cupom)
    const mensagemTextarea = document.getElementById('editarMensagem');
    if (mensagemTextarea && produtoAtualData && produtoAtualData.final_message) {
      mensagemTextarea.value = produtoAtualData.final_message;
    }
    return;
  }

  previewElement.style.display = 'block';

  // Formatar valores para exibição (com vírgula)
  const formatarPreco = (valor) => valor.toFixed(2).replace('.', ',');

  previewElement.innerHTML = `
    <div style="
      background: #f0f9ff;
      border: 2px solid #667eea;
      border-radius: 8px;
      padding: 15px;
      margin-top: 15px;
    ">
      <div style="font-weight: 600; color: #667eea; margin-bottom: 10px;">
        💰 Preview do Cupom:
      </div>
      <div style="color: #666; font-size: 14px; line-height: 1.6;">
        <div>🏷️ Preço Original: <span style="text-decoration: line-through;">R$ ${formatarPreco(cupomData.precoOriginal)}</span></div>
        <div>🎟️ Cupom: <strong>${cupomData.codigo}</strong> (${cupomData.porcentagem}%)</div>
        <div>💸 Desconto: R$ ${formatarPreco(cupomData.desconto)}</div>
        <div style="font-size: 16px; font-weight: 600; color: #10b981; margin-top: 8px;">
          ✅ Preço Final: R$ ${formatarPreco(cupomData.valorFinal)}
        </div>
      </div>
    </div>
  `;

  // 🎟️ ATUALIZAR MENSAGEM NO TEXTAREA COM CUPOM
  const mensagemTextarea = document.getElementById('editarMensagem');
  if (mensagemTextarea && produtoAtualData) {
    const mensagemOriginal = produtoAtualData.final_message || '';

    // Reformatar mensagem substituindo preço e cupom
    let novaMensagem = mensagemOriginal;

    // Substituir linha "De ~R$ XXX~ → Por *R$ YYY*"
    const regexPreco = /De ~R\$ [\d,.]+~ → Por \*R\$ [\d,.]+\*/g;
    const novaLinhaPreco = `De ~R$ ${formatarPreco(cupomData.precoOriginal)}~ → Por *R$ ${formatarPreco(cupomData.valorFinal)}*`;

    if (regexPreco.test(mensagemOriginal)) {
      novaMensagem = novaMensagem.replace(regexPreco, novaLinhaPreco);
    }

    // Substituir linha "Use o cupom: *XXX*"
    const regexCupom = /🎟️ Use o cupom: \*[^*]+\*/g;
    const novaLinhaCupom = `🎟️ Use o cupom: *${cupomData.codigo}*`;

    if (regexCupom.test(mensagemOriginal)) {
      novaMensagem = novaMensagem.replace(regexCupom, novaLinhaCupom);
    } else {
      // Se não tem linha de cupom, adicionar depois da linha de preço
      const regexPrecoSimples = /(De ~R\$ [\d,.]+~ → Por \*R\$ [\d,.]+\*)/g;
      if (regexPrecoSimples.test(novaMensagem)) {
        novaMensagem = novaMensagem.replace(regexPrecoSimples, `$1\n${novaLinhaCupom}`);
      }
    }

    mensagemTextarea.value = novaMensagem;
  }
}

// Carregar cupons quando a página carregar
document.addEventListener('DOMContentLoaded', () => {
  carregarCuponsAtivos();

  // Observer para recarregar cupons quando abrir modal de edição
  const editModal = document.getElementById('editarModal');
  if (editModal) {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.target.style.display === 'block') {
          carregarCuponsAtivos();
        }
      });
    });

    observer.observe(editModal, {
      attributes: true,
      attributeFilter: ['style']
    });
  }
});

console.log('✅ Sistema de cupons carregado');