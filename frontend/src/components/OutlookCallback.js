import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Card, CardContent } from './ui/card';
import { CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';

const OutlookCallback = () => {
  const location = useLocation();
  const [status, setStatus] = useState('processing'); // processing, success, error
  const [message, setMessage] = useState('Outlook bağlantısı işleniyor...');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Parse URL parameters
        const searchParams = new URLSearchParams(location.search);
        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const error = searchParams.get('error');

        if (error) {
          setStatus('error');
          setMessage('Outlook bağlantısı iptal edildi veya hata oluştu.');
          
          // Send error to parent window
          if (window.opener) {
            window.opener.postMessage({
              type: 'OUTLOOK_AUTH_ERROR',
              error: error
            }, '*');
            window.close();
          }
          return;
        }

        if (!code || !state) {
          setStatus('error');
          setMessage('Geçersiz callback parametreleri.');
          
          if (window.opener) {
            window.opener.postMessage({
              type: 'OUTLOOK_AUTH_ERROR',
              error: 'Invalid callback parameters'
            }, '*');
            window.close();
          }
          return;
        }

        // Send success to parent window
        if (window.opener) {
          window.opener.postMessage({
            type: 'OUTLOOK_AUTH_SUCCESS',
            code: code,
            state: state
          }, '*');
          
          setStatus('success');
          setMessage('Outlook hesabı başarıyla bağlandı! Bu pencere kapatılıyor...');
          
          // Close popup after a short delay
          setTimeout(() => {
            window.close();
          }, 2000);
        } else {
          // If not in popup, show message
          setStatus('success');
          setMessage('Outlook hesabı başarıyla bağlandı! Ana sayfaya dönebilirsiniz.');
        }

      } catch (err) {
        console.error('Callback processing error:', err);
        setStatus('error');
        setMessage('Callback işlenirken hata oluştu.');
        
        if (window.opener) {
          window.opener.postMessage({
            type: 'OUTLOOK_AUTH_ERROR',
            error: 'Callback processing failed'
          }, '*');
          window.close();
        }
      }
    };

    handleCallback();
  }, [location]);

  const getIcon = () => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-8 h-8 text-green-600" />;
      case 'error':
        return <AlertCircle className="w-8 h-8 text-red-600" />;
      default:
        return <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />;
    }
  };

  const getCardColor = () => {
    switch (status) {
      case 'success':
        return 'border-green-200 bg-green-50';
      case 'error':
        return 'border-red-200 bg-red-50';
      default:
        return 'border-blue-200 bg-blue-50';
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className={`w-full max-w-md ${getCardColor()}`}>
        <CardContent className="p-8 text-center">
          <div className="flex justify-center mb-4">
            {getIcon()}
          </div>
          
          <h2 className="text-xl font-semibold text-slate-800 mb-2">
            Outlook Hesap Bağlantısı
          </h2>
          
          <p className="text-slate-600">
            {message}
          </p>
          
          {status === 'processing' && (
            <div className="mt-4">
              <div className="w-full bg-blue-200 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{width: '70%'}}></div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default OutlookCallback;