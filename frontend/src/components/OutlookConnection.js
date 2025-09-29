import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import { 
  Plus, 
  Mail, 
  Settings, 
  Trash2, 
  RefreshCw, 
  CheckCircle, 
  AlertCircle,
  ExternalLink,
  Calendar,
  User
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const OutlookConnection = ({ user, onAccountsUpdate }) => {
  const [connectedAccounts, setConnectedAccounts] = useState([]);
  const [connectDialogOpen, setConnectDialogOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [authUrl, setAuthUrl] = useState('');
  const [syncingAccount, setSyncingAccount] = useState(null);

  useEffect(() => {
    fetchConnectedAccounts();
    
    // Listen for OAuth callback
    const handleCallback = (event) => {
      if (event.data?.type === 'OUTLOOK_AUTH_SUCCESS') {
        handleAuthCallback(event.data.code, event.data.state);
      }
    };

    window.addEventListener('message', handleCallback);
    return () => window.removeEventListener('message', handleCallback);
  }, []);

  const getAuthHeaders = () => ({
    'Authorization': `Bearer ${localStorage.getItem('token')}`,
    'Content-Type': 'application/json'
  });

  const fetchConnectedAccounts = async () => {
    try {
      const response = await axios.get(`${API}/outlook/accounts`, {
        headers: getAuthHeaders()
      });
      setConnectedAccounts(response.data.accounts || []);
      if (onAccountsUpdate) {
        onAccountsUpdate(response.data.accounts || []);
      }
    } catch (error) {
      console.error('Error fetching connected accounts:', error);
    }
  };

  const initiateOutlookConnection = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/outlook/auth-url`, {
        headers: getAuthHeaders()
      });
      
      setAuthUrl(response.data.auth_url);
      
      // Open OAuth popup
      const popup = window.open(
        response.data.auth_url,
        'outlookAuth',
        'width=600,height=700,scrollbars=yes,resizable=yes'
      );

      // Monitor popup
      const checkClosed = setInterval(() => {
        if (popup.closed) {
          clearInterval(checkClosed);
          setLoading(false);
          setConnectDialogOpen(false);
        }
      }, 1000);

    } catch (error) {
      console.error('Error initiating Outlook connection:', error);
      toast.error('Outlook bağlantısı başlatılamadı');
      setLoading(false);
    }
  };

  const handleAuthCallback = async (code, state) => {
    try {
      setLoading(true);
      
      const response = await axios.post(`${API}/outlook/connect-account`, {
        code,
        state
      }, {
        headers: getAuthHeaders()
      });

      toast.success('Outlook hesabı başarıyla bağlandı!');
      await fetchConnectedAccounts();
      setConnectDialogOpen(false);
      
    } catch (error) {
      console.error('Error connecting account:', error);
      let errorMsg = 'Hesap bağlantısı başarısız';
      
      if (error.response?.data?.detail) {
        // Handle both string and object error responses
        const detail = error.response.data.detail;
        if (typeof detail === 'string') {
          errorMsg = detail;
        } else if (typeof detail === 'object' && detail.msg) {
          errorMsg = detail.msg;
        } else if (typeof detail === 'object') {
          errorMsg = JSON.stringify(detail);
        }
      }
      
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const syncAccount = async (accountId) => {
    try {
      setSyncingAccount(accountId);
      
      const response = await axios.post(`${API}/outlook/sync`, null, {
        params: { account_id: accountId },
        headers: getAuthHeaders()
      });

      toast.success(`${response.data.total_synced} e-posta senkronize edildi`);
      await fetchConnectedAccounts();
      
    } catch (error) {
      console.error('Error syncing account:', error);
      const errorMsg = error.response?.data?.detail || 'Senkronizasyon başarısız';
      toast.error(errorMsg);
    } finally {
      setSyncingAccount(null);
    }
  };

  const disconnectAccount = async (accountId) => {
    try {
      await axios.delete(`${API}/outlook/accounts/${accountId}`, {
        headers: getAuthHeaders()
      });
      
      toast.success('Hesap bağlantısı kesildi');
      await fetchConnectedAccounts();
      
    } catch (error) {
      console.error('Error disconnecting account:', error);
      toast.error('Hesap bağlantısı kesilemedi');
    }
  };

  const formatLastSync = (lastSync) => {
    if (!lastSync) return 'Hiç senkronize edilmedi';
    
    const date = new Date(lastSync);
    const now = new Date();
    const diffMinutes = Math.floor((now - date) / (1000 * 60));
    
    if (diffMinutes < 1) return 'Az önce';
    if (diffMinutes < 60) return `${diffMinutes} dakika önce`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)} saat önce`;
    return date.toLocaleDateString('tr-TR');
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
            Bağlı Outlook Hesapları
          </h3>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            E-postalarınızı senkronize etmek için Outlook hesaplarınızı bağlayın
          </p>
        </div>
        
        <Button 
          onClick={() => setConnectDialogOpen(true)}
          className="bg-[#0078d4] hover:bg-[#106ebe] text-white"
          disabled={loading}
        >
          <Plus className="w-4 h-4 mr-2" />
          Outlook Bağla
        </Button>
      </div>

      {/* Connected Accounts List */}
      <div className="grid gap-4">
        {connectedAccounts.length === 0 ? (
          <Card className="border-dashed border-2">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Mail className="w-12 h-12 text-slate-400 mb-4" />
              <p className="text-slate-600 dark:text-slate-400 text-center">
                Henüz bağlı Outlook hesabınız yok.<br />
                İlk hesabınızı bağlamak için yukarıdaki butona tıklayın.
              </p>
            </CardContent>
          </Card>
        ) : (
          connectedAccounts.map((account) => (
            <Card key={account.id} className="border border-slate-200 dark:border-slate-700">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-[#0078d4] rounded-full flex items-center justify-center">
                      <Mail className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h4 className="font-medium text-slate-900 dark:text-white">
                          {account.display_name || 'Outlook Kullanıcısı'}
                        </h4>
                        <Badge variant="secondary" className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Bağlı
                        </Badge>
                      </div>
                      <p className="text-sm text-slate-600 dark:text-slate-400">
                        {account.email}
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-500">
                        Son senkronizasyon: {formatLastSync(account.last_sync)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => syncAccount(account.id)}
                      disabled={syncingAccount === account.id}
                      className="text-blue-600 border-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:border-blue-400"
                    >
                      {syncingAccount === account.id ? (
                        <RefreshCw className="w-4 h-4 animate-spin" />
                      ) : (
                        <RefreshCw className="w-4 h-4" />
                      )}
                      Senkronize Et
                    </Button>
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => disconnectAccount(account.id)}
                      className="text-red-600 border-red-600 hover:bg-red-50 dark:text-red-400 dark:border-red-400"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Connect Dialog */}
      <Dialog open={connectDialogOpen} onOpenChange={setConnectDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-[#0078d4] rounded-full flex items-center justify-center">
                <Mail className="w-4 h-4 text-white" />
              </div>
              <span>Outlook Hesabı Bağla</span>
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <CheckCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                <div className="space-y-2">
                  <h4 className="font-medium text-blue-900 dark:text-blue-100">
                    Microsoft Outlook ile güvenli bağlantı
                  </h4>
                  <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
                    <li>• Kişisel ve kurumsal hesaplar desteklenir</li>
                    <li>• Tüm klasörler senkronize edilir (Gelen, Gönderilen, Spam)</li>
                    <li>• OAuth2 ile güvenli kimlik doğrulama</li>
                    <li>• Şifreleriniz saklanmaz</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="flex space-x-2">
              <Button
                onClick={initiateOutlookConnection}
                disabled={loading}
                className="flex-1 bg-[#0078d4] hover:bg-[#106ebe] text-white"
              >
                {loading ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <ExternalLink className="w-4 h-4 mr-2" />
                )}
                Microsoft ile Bağlan
              </Button>
              
              <Button
                variant="outline"
                onClick={() => setConnectDialogOpen(false)}
                disabled={loading}
              >
                İptal
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default OutlookConnection;