import React, { useEffect, useRef } from 'react';
import DOMPurify from 'dompurify';

const SafeHTMLRenderer = ({ htmlContent, className = '' }) => {
  const iframeRef = useRef(null);

  useEffect(() => {
    if (!htmlContent || !iframeRef.current) return;

    // DOMPurify konfigürasyonu - img etiketlerine ve src'lere izin ver
    const cleanHTML = DOMPurify.sanitize(htmlContent, {
      ALLOWED_TAGS: [
        'div', 'span', 'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'a', 'img', 'table', 'thead', 'tbody', 'tr', 'td', 'th',
        'font', 'center', 'pre', 'code', 'hr', 'small', 'sub', 'sup'
      ],
      ALLOWED_ATTR: [
        'href', 'src', 'alt', 'title', 'width', 'height', 'style', 'color', 'bgcolor', 
        'align', 'valign', 'cellspacing', 'cellpadding', 'border', 'class', 'id',
        'target', 'rel', 'face', 'size'
      ],
      ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|cid|xmpp|data):|[^a-z]|[a-z+.-]+(?:[^a-z+.-]|$))/i,
      // Resimlerin otomatik yüklenmesi için
      FORBID_ATTR: [],
      // Script'leri tamamen engelle
      FORBID_TAGS: ['script', 'object', 'embed', 'form', 'input', 'button']
    });

    // Iframe için HTML template'i
    const iframeHTML = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <style>
            body { 
              margin: 0; 
              padding: 16px; 
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
              line-height: 1.6;
              color: #374151;
              background: #ffffff;
              overflow-wrap: break-word;
              word-wrap: break-word;
            }
            img {
              max-width: 100% !important;
              height: auto !important;
              border-radius: 4px;
              box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            a {
              color: #3b82f6;
              text-decoration: none;
            }
            a:hover {
              text-decoration: underline;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              margin: 8px 0;
            }
            td, th {
              padding: 8px;
              border: 1px solid #e5e7eb;
            }
            blockquote {
              border-left: 4px solid #e5e7eb;
              margin: 16px 0;
              padding-left: 16px;
              color: #6b7280;
            }
            pre {
              background: #f3f4f6;
              padding: 12px;
              border-radius: 4px;
              overflow-x: auto;
            }
          </style>
        </head>
        <body>
          ${cleanHTML}
        </body>
      </html>
    `;

    // Iframe'e HTML'i yükle
    const iframe = iframeRef.current;
    const doc = iframe.contentDocument || iframe.contentWindow.document;
    doc.open();
    doc.write(iframeHTML);
    doc.close();

    // Iframe yüksekliğini içeriğe göre ayarla
    const resizeIframe = () => {
      try {
        const body = doc.body;
        if (body) {
          const height = Math.max(
            body.scrollHeight,
            body.offsetHeight,
            doc.documentElement.clientHeight,
            doc.documentElement.scrollHeight,
            doc.documentElement.offsetHeight
          );
          iframe.style.height = Math.max(height, 100) + 'px';
        }
      } catch (error) {
        // Cross-origin hatalarını yoksay
        iframe.style.height = '300px';
      }
    };

    // Yükleme tamamlandığında boyutlandır
    iframe.onload = resizeIframe;
    
    // İçerik değiştikçe boyutlandır
    setTimeout(resizeIframe, 100);
    setTimeout(resizeIframe, 500);

  }, [htmlContent]);

  if (!htmlContent) {
    return <div className="text-gray-500 italic">İçerik bulunamadı</div>;
  }

  return (
    <iframe
      ref={iframeRef}
      className={`w-full border-0 ${className}`}
      style={{ minHeight: '100px' }}
      sandbox="allow-same-origin"
      title="E-posta İçeriği"
    />
  );
};

export default SafeHTMLRenderer;