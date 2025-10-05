import React, { useMemo } from 'react';
import DOMPurify from 'dompurify';

const SafeHTMLRenderer = ({ htmlContent, className = '' }) => {
  // Debug: Content'i console'a yazdır
  console.log('SafeHTMLRenderer received content:', htmlContent?.substring(0, 200) + '...');
  console.log('Content type check:', typeof htmlContent);

  const sanitizedHTML = useMemo(() => {
    if (!htmlContent) {
      console.log('SafeHTMLRenderer: No content provided');
      return '';
    }

    try {
      // DOMPurify ile HTML'i temizle
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
        ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|cid|xmpp|data|blob):|[^a-z]|[a-z+.-]+(?:[^a-z+.-]|$))/i,
        FORBID_TAGS: ['script', 'object', 'embed', 'form', 'input', 'button'],
        // HTML'i işlemek için gereken ayarlar
        KEEP_CONTENT: true,
        RETURN_DOM: false,
        RETURN_DOM_FRAGMENT: false,
        RETURN_TRUSTED_TYPE: false
      });

      console.log('SafeHTMLRenderer: Cleaned HTML length:', cleanHTML.length);
      return cleanHTML;
    } catch (error) {
      console.error('SafeHTMLRenderer: DOMPurify error:', error);
      return '<p style="color: red;">HTML içeriği işlenirken hata oluştu.</p>';
    }
  }, [htmlContent]);

  if (!htmlContent) {
    return (
      <div className={`text-gray-500 italic p-4 ${className}`}>
        İçerik bulunamadı
      </div>
    );
  }

  return (
    <div 
      className={`safe-html-content prose prose-slate max-w-none ${className}`}
      style={{
        fontSize: '14px',
        lineHeight: '1.6',
        color: '#374151'
      }}
      dangerouslySetInnerHTML={{ __html: sanitizedHTML }}
    />
  );
};

export default SafeHTMLRenderer;