import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent } from './ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { toast } from 'sonner';
import { useTheme } from '../contexts/ThemeContext';
import { useLanguage } from '../contexts/LanguageContext';
import { 
  Mail, 
  Search, 
  Settings, 
  LogOut, 
  Inbox, 
  Send, 
  Archive, 
  Trash2, 
  AlertTriangle, 
  RefreshCw, 
  Upload, 
  Download,
  Flag,
  Circle,
  HardDrive,
  MoreVertical,
  Trash,
  AlertCircle,
  Link2,
  CheckCircle,
  Globe,
  Palette,
  Clock,
  Save,
  FileText,
  Zap,
  Plus,
  Paperclip,
  User,
  Building2,
  ChevronRight,
  Calendar,
  BarChart3,
  Image,
  FileType,
  ArrowLeft,
  ArrowRight,
  MessageSquare
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = ({ user, onLogout }) => {
  const { theme, setTheme } = useTheme();
  const { language, setLanguage, t } = useLanguage();
  
  const [selectedFolder, setSelectedFolder] = useState('inbox');
  const [emails, setEmails] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [emailDetailOpen, setEmailDetailOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [accountConnectOpen, setAccountConnectOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [lastSync, setLastSync] = useState(null);
  const [folders, setFolders] = useState({
    all: { name: t('navigation.allMails'), count: 0, icon: Archive },
    inbox: { name: t('navigation.inbox'), count: 0, icon: Inbox },
    sent: { name: t('navigation.sent'), count: 0, icon: Send },
    deleted: { name: t('navigation.deleted'), count: 0, icon: Trash2 },
    spam: { name: t('navigation.spam'), count: 0, icon: AlertTriangle }
  });
  const [storageInfo, setStorageInfo] = useState({ totalEmails: 0, totalSize: 0 });
  const [settings, setSettings] = useState({
    theme: theme,
    language: language,
    autoSync: false,
    autoSyncInterval: 10
  });
  const [connectedAccounts, setConnectedAccounts] = useState([]);
  const [newOutlookEmail, setNewOutlookEmail] = useState('');
  const [newOutlookName, setNewOutlookName] = useState('');

  // Update folder names when language changes
  useEffect(() => {
    setFolders(prev => ({
      ...prev,
      all: { ...prev.all, name: t('navigation.allMails') },
      inbox: { ...prev.inbox, name: t('navigation.inbox') },
      sent: { ...prev.sent, name: t('navigation.sent') },
      deleted: { ...prev.deleted, name: t('navigation.deleted') },
      spam: { ...prev.spam, name: t('navigation.spam') }
    }));
  }, [language, t]);

  useEffect(() => {
    loadEmails();
    loadStorageInfo();
    loadLastSync();
    loadSettings();
    loadConnectedAccounts();
  }, [selectedFolder]);

  const loadEmails = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/emails?folder=${selectedFolder}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEmails(response.data.emails || []);
      
      // Update folder counts
      const folderCounts = response.data.folderCounts || {};
      setFolders(prev => ({
        ...prev,
        inbox: { ...prev.inbox, count: folderCounts.inbox || 0 },
        sent: { ...prev.sent, count: folderCounts.sent || 0 },
        all: { ...prev.all, count: folderCounts.all || 0 },
        deleted: { ...prev.deleted, count: folderCounts.deleted || 0 },
        spam: { ...prev.spam, count: folderCounts.spam || 0 }
      }));
    } catch (error) {
      toast.error(t('notifications.emailsLoadError'));
    }
  };

  const loadStorageInfo = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/storage-info`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStorageInfo(response.data);
    } catch (error) {
      console.error('Storage info load error:', error);
    }
  };

  const loadLastSync = () => {
    const stored = localStorage.getItem('lastSync');
    if (stored) {
      setLastSync(new Date(stored));
    }
  };

  const loadSettings = () => {
    const savedSettings = localStorage.getItem('userSettings');
    if (savedSettings) {
      const parsed = JSON.parse(savedSettings);
      setSettings({
        ...parsed,
        theme: theme,
        language: language
      });
    }
  };

  const loadConnectedAccounts = async () => {
    try {
      // First try to load from localStorage
      const savedAccounts = localStorage.getItem('connectedAccounts');
      if (savedAccounts) {
        setConnectedAccounts(JSON.parse(savedAccounts));
        return;
      }

      // Fallback to backend
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/connected-accounts`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setConnectedAccounts(response.data.accounts || []);
    } catch (error) {
      console.error('Connected accounts load error:', error);
    }
  };

  const handleDisconnectAccount = async (accountId, accountType) => {
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/connected-accounts/${accountId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setConnectedAccounts(prev => {
        const updated = prev.filter(acc => acc.id !== accountId);
        localStorage.setItem('connectedAccounts', JSON.stringify(updated));
        return updated;
      });
      toast.success(t('notifications.accountDisconnected').replace('{type}', accountType));
    } catch (error) {
      toast.error(`${accountType} hesabı bağlantısı kesilemedi`);
    }
  };

  const handleSync = async () => {
    // Check if any accounts are connected
    if (connectedAccounts.length === 0) {
      toast.error(t('notifications.noAccountsConnected'), {
        duration: 4000,
        action: {
          label: t('dashboard.connectAccount'),
          onClick: () => setAccountConnectOpen(true)
        }
      });
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/sync-emails`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const now = new Date();
      setLastSync(now);
      localStorage.setItem('lastSync', now.toISOString());
      
      toast.success(t('notifications.syncSuccess'), {
        description: `${connectedAccounts.length} hesaptan senkronizasyon yapıldı`
      });
      loadEmails();
      loadStorageInfo();
    } catch (error) {
      toast.error(t('notifications.syncError'));
    }
    setLoading(false);
  };

  const handleEmailClick = (email) => {
    setSelectedEmail(email);
    setEmailDetailOpen(true);
    
    // Mark as read if unread
    if (!email.read) {
      markAsRead(email.id);
    }
  };

  const markAsRead = async (emailId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/emails/${emailId}/read`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      loadEmails();
    } catch (error) {
      console.error('Mark as read error:', error);
    }
  };

  const handleDeleteEmail = async () => {
    if (!selectedEmail) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/emails/${selectedEmail.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success(t('notifications.deleteSuccess'));
      setDeleteConfirmOpen(false);
      setEmailDetailOpen(false);
      loadEmails();
      loadStorageInfo();
    } catch (error) {
      toast.error(t('notifications.deleteError'));
    }
  };

  const handleImport = async (file) => {
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/import-emails`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          toast.info(`${t('common.loading')}: %${percentCompleted}`);
        }
      });
      
      toast.success(t('notifications.importSuccess').replace('{count}', response.data.count));
      setImportOpen(false);
      loadEmails();
      loadStorageInfo();
    } catch (error) {
      toast.error(t('notifications.importError') + ': ' + (error.response?.data?.detail || t('common.error')));
    }
    setLoading(false);
  };

  const handleExport = async (format) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/export-emails`, 
        { format, folder: selectedFolder },
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );
      
      // Create download link
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `postadepo-emails-${selectedFolder}-${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success(t('notifications.exportSuccess'));
      setExportOpen(false);
    } catch (error) {
      toast.error(t('notifications.exportError'));
    }
    setLoading(false);
  };

  const handleSaveSettings = () => {
    // Save theme and language to contexts
    if (settings.theme !== theme) {
      setTheme(settings.theme);
    }
    if (settings.language !== language) {
      setLanguage(settings.language);
    }
    
    localStorage.setItem('userSettings', JSON.stringify(settings));
    toast.success(t('notifications.settingsSaved'));
    setSettingsOpen(false);
    
    // If auto sync is enabled, set up interval
    if (settings.autoSync) {
      const interval = settings.autoSyncInterval * 60 * 1000; // Convert to milliseconds
      setInterval(() => {
        handleSync();
      }, interval);
      toast.info(t('notifications.autoSyncEnabled').replace('{interval}', settings.autoSyncInterval));
    }
  };

  const handleConnectOutlook = async (email, name) => {
    if (!email || !email.includes('@')) {
      toast.error('Geçerli bir email adresi girin');
      return;
    }
    
    setLoading(true);
    toast.info(t('notifications.outlookConnecting'));
    
    try {
      const token = localStorage.getItem('token');
      
      // Call backend API to connect Outlook
      const response = await axios.post(`${API}/connect-account`, 
        { 
          type: 'outlook', 
          email: email,
          name: name || email.split('@')[0].replace('.', ' ')
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // Update local state
      setConnectedAccounts(prev => {
        const updated = [...prev, response.data.account];
        localStorage.setItem('connectedAccounts', JSON.stringify(updated));
        return updated;
      });
      
      toast.success(t('notifications.outlookConnected'));
      setLoading(false);
      return true; // Başarılı
    } catch (error) {
      if (error.response?.status === 400) {
        toast.error(error.response.data?.detail || 'Bu Outlook hesabı zaten bağlı');
      } else {
        toast.error(t('notifications.outlookError'));
      }
      setLoading(false);
      return false; // Başarısız
    }
  };

  // Gmail fonksiyonu kaldırıldı - sadece Outlook desteği

  const filteredEmails = emails.filter(email => {
    if (selectedFolder !== 'all' || !searchTerm) return true;
    return email.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
           email.sender.toLowerCase().includes(searchTerm.toLowerCase()) ||
           email.content.toLowerCase().includes(searchTerm.toLowerCase());
  });

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString(language === 'tr' ? 'tr-TR' : 'en-US', {
      day: '2-digit',
      month: '2-digit', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 flex">
      {/* Sidebar */}
      <div className="w-80 bg-white/90 backdrop-blur-sm border-r border-slate-200 flex flex-col shadow-lg sidebar">
        {/* Header */}
        <div className="p-2 border-b border-slate-200">
          <div className="flex flex-col items-center">
            <img 
              src="https://customer-assets.emergentagent.com/job_240f2e1c-9c13-45be-8f51-23631a027e43/artifacts/kpwl9rr8_postadepo_logo_transparent.png"
              alt="PostaDepo"
              className="w-48 h-48"
            />
            <p className="text-sm text-slate-600 text-center -mt-1">{user?.email}</p>
          </div>
          
          <div className="flex space-x-2">
            <Button 
              onClick={handleSync}
              disabled={loading}
              className="flex-1 h-10 bg-[#2c5282] hover:bg-[#1a365d] text-white rounded-lg text-sm"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              {t('dashboard.sync')}
            </Button>
            
            <Button 
              onClick={() => setSettingsOpen(true)}
              variant="outline"
              className="h-10 px-3 border-slate-300 hover:bg-slate-100 rounded-lg"
            >
              <Settings className="w-4 h-4" />
            </Button>
          </div>
          
          {lastSync && (
            <p className="text-xs text-slate-500 mt-2">
              {t('dashboard.lastSync')}: {formatDate(lastSync)}
            </p>
          )}
        </div>

        {/* Navigation */}
        <div className="flex-1 p-4">
          <nav className="space-y-2">
            {Object.entries(folders).map(([key, folder]) => {
              const IconComponent = folder.icon;
              return (
                <button
                  key={key}
                  onClick={() => setSelectedFolder(key)}
                  className={`w-full flex items-center justify-between p-3 rounded-lg text-left transition-all ${
                    selectedFolder === key 
                      ? 'bg-[#2c5282] text-white shadow-lg transform scale-[1.02]' 
                      : 'hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <IconComponent className="w-5 h-5" />
                    <span className="font-medium">{folder.name}</span>
                  </div>
                  <span className={`text-sm px-2 py-1 rounded-full ${
                    selectedFolder === key 
                      ? 'bg-white/20 text-white' 
                      : 'bg-slate-200 text-slate-600'
                  }`}>
                    {folder.count}
                  </span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Storage Info */}
        <div className="p-4 border-t border-slate-200 bg-gradient-to-r from-slate-50 to-blue-50">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center space-x-2">
                <HardDrive className="w-4 h-4 text-slate-500" />
                <span className="text-slate-600">{t('dashboard.totalMails')}</span>
              </div>
              <span className="font-semibold text-slate-800">{storageInfo.totalEmails}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-600">{t('dashboard.storage')}</span>
              <span className="font-semibold text-slate-800">{formatSize(storageInfo.totalSize)}</span>
            </div>
          </div>
        </div>

        {/* Colorful Action Buttons */}
        <div className="p-4 border-t border-slate-200 space-y-2 bg-gradient-to-r from-purple-50 to-pink-50">
          <div className="flex space-x-2">
            <Button 
              onClick={() => setImportOpen(true)}
              className="flex-1 h-10 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white rounded-lg text-sm shadow-lg"
            >
              <Upload className="w-4 h-4 mr-2" />
              {t('dashboard.import')}
            </Button>
            <Button 
              onClick={() => setExportOpen(true)}
              className="flex-1 h-10 bg-gradient-to-r from-purple-500 to-violet-600 hover:from-purple-600 hover:to-violet-700 text-white rounded-lg text-sm shadow-lg"
            >
              <Download className="w-4 h-4 mr-2" />
              {t('dashboard.export')}
            </Button>
          </div>
          
          <Button 
            onClick={() => setAccountConnectOpen(true)}
            className="w-full h-10 bg-gradient-to-r from-blue-500 to-cyan-600 hover:from-blue-600 hover:to-cyan-700 text-white rounded-lg shadow-lg"
          >
            <Link2 className="w-4 h-4 mr-2" />
            {connectedAccounts.length > 0 
              ? `${t('dashboard.connectedAccounts')} (${connectedAccounts.length})`
              : t('dashboard.connectAccount')
            }
          </Button>
          
          <Button 
            onClick={onLogout}
            variant="outline" 
            className="w-full h-10 border-red-300 text-red-600 hover:bg-red-50 rounded-lg"
          >
            <LogOut className="w-4 h-4 mr-2" />
            {t('common.logout')}
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Search Bar */}
        <div className="bg-white/90 backdrop-blur-sm border-b border-slate-200 p-4 shadow-sm">
          <div className="max-w-2xl">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
              <Input
                type="text"
                placeholder={selectedFolder === 'all' ? t('dashboard.searchPlaceholder') : t('dashboard.searchDisabled')}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                disabled={selectedFolder !== 'all'}
                className={`pl-10 h-12 bg-white/70 border-slate-200 focus:border-[#2c5282] focus:ring-[#2c5282] rounded-lg ${
                  selectedFolder !== 'all' ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              />
            </div>
          </div>
        </div>

        {/* Email List */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-2">
            {filteredEmails.length === 0 ? (
              <div className="text-center py-12">
                <Mail className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                <p className="text-slate-500 text-lg">{t('dashboard.noEmails')}</p>
              </div>
            ) : (
              filteredEmails.map((email) => (
                <Card 
                  key={email.id} 
                  className={`cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-[1.01] bg-white/80 backdrop-blur-sm border-0 ${
                    email.important ? 'border-l-4 border-l-red-500 bg-red-50/50' : ''
                  }`}
                  onClick={() => handleEmailClick(email)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-2">
                        {!email.read && (
                          <Circle className="w-3 h-3 text-blue-500 fill-current" />
                        )}
                        {email.important && (
                          <Flag className="w-4 h-4 text-red-500" />
                        )}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <p className={`text-sm truncate ${!email.read ? 'font-semibold text-slate-900' : 'text-slate-700'}`}>
                            {email.sender}
                          </p>
                          <div className="flex items-center space-x-2">
                            <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded-full">
                              {formatSize(email.size || 1024)}
                            </span>
                            <p className="text-xs text-slate-500">{formatDate(email.date)}</p>
                          </div>
                        </div>
                        <p className={`text-sm truncate mb-1 ${!email.read ? 'font-medium text-slate-800' : 'text-slate-600'}`}>
                          {email.subject}
                        </p>
                        <p className="text-xs text-slate-500 truncate">{email.preview}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Email Detail Modal */}
      <Dialog open={emailDetailOpen} onOpenChange={setEmailDetailOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto backdrop-blur-md bg-white/95">
          <DialogHeader>
            <DialogTitle className="text-xl text-slate-800">{selectedEmail?.subject}</DialogTitle>
          </DialogHeader>
          {selectedEmail && (
            <div className="space-y-4">
              <div className="bg-slate-50 p-4 rounded-lg">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <p className="font-semibold text-slate-800">{selectedEmail.sender}</p>
                    <p className="text-sm text-slate-600">{selectedEmail.recipient}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-slate-500">{formatDate(selectedEmail.date)}</p>
                    <span className="inline-block text-xs text-slate-500 bg-slate-200 px-2 py-1 rounded-full mt-1">
                      {t('email.size')}: {formatSize(selectedEmail.size || 1024)}
                    </span>
                  </div>
                </div>
                {selectedEmail.important && (
                  <div className="flex items-center space-x-2 text-red-600">
                    <Flag className="w-4 h-4" />
                    <span className="text-sm font-medium">{t('email.important')}</span>
                  </div>
                )}
              </div>
              <div className="prose max-w-none">
                <div className="whitespace-pre-wrap text-slate-700 leading-relaxed">
                  {selectedEmail.content}
                </div>
              </div>
              
              {/* Move delete button to top-right corner */}
              <div className="flex justify-between items-center pt-4 border-t">
                <div className="text-sm text-slate-500">
                  {t('email.actions')}
                </div>
                <Button
                  onClick={() => setDeleteConfirmOpen(true)}
                  variant="outline"
                  size="sm"
                  className="border-red-300 text-red-600 hover:bg-red-50"
                >
                  <Trash className="w-4 h-4 mr-2" />
                  {t('email.permanentlyDelete')}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Modal */}
      <Dialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <DialogContent className="sm:max-w-md backdrop-blur-md bg-white/95">
          <DialogHeader>
            <DialogTitle className="text-center text-red-700 flex items-center justify-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              {t('common.delete')} {t('common.email')}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            <div className="text-center">
              <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
              <p className="text-slate-700 mb-2">{t('email.deleteConfirm')}</p>
              <p className="text-sm text-slate-500">{t('email.deleteWarning')}</p>
            </div>
            <div className="flex space-x-2">
              <Button 
                onClick={() => setDeleteConfirmOpen(false)}
                variant="outline" 
                className="flex-1"
              >
                {t('common.cancel')}
              </Button>
              <Button 
                onClick={handleDeleteEmail}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white"
              >
                {t('email.yes')}, {t('common.delete')}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Enhanced Settings Modal */}
      <Dialog open={settingsOpen} onOpenChange={setSettingsOpen}>
        <DialogContent className="sm:max-w-md backdrop-blur-md bg-white/95">
          <DialogHeader>
            <DialogTitle className="text-center text-slate-800 flex items-center justify-center gap-2">
              <Settings className="w-5 h-5" />
              {t('settings.title')}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-6 pt-4">
            <div className="text-center">
              <img 
                src="https://customer-assets.emergentagent.com/job_240f2e1c-9c13-45be-8f51-23631a027e43/artifacts/kpwl9rr8_postadepo_logo_transparent.png"
                alt="PostaDepo"
                className="w-20 h-20 mx-auto mb-4"
              />
              <h3 className="text-lg font-semibold text-slate-800">PostaDepo</h3>
              <p className="text-sm text-slate-600">E-posta Yönetim Sistemi</p>
              <p className="text-xs text-slate-500 mt-2">{t('settings.version')}</p>
            </div>
            
            {/* Theme Settings */}
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Palette className="w-4 h-4 text-slate-600" />
                <label className="text-sm font-medium text-slate-700">{t('settings.theme')}</label>
              </div>
              <select 
                value={settings.theme}
                onChange={(e) => setSettings({...settings, theme: e.target.value})}
                className="w-full p-2 border border-slate-300 rounded-lg focus:border-[#2c5282] focus:ring-1 focus:ring-[#2c5282]"
              >
                <option value="light">{t('settings.themes.light')}</option>
                <option value="dark">{t('settings.themes.dark')}</option>
                <option value="auto">{t('settings.themes.auto')}</option>
              </select>
            </div>

            {/* Language Settings */}
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Globe className="w-4 h-4 text-slate-600" />
                <label className="text-sm font-medium text-slate-700">{t('settings.language')}</label>
              </div>
              <select 
                value={settings.language}
                onChange={(e) => setSettings({...settings, language: e.target.value})}
                className="w-full p-2 border border-slate-300 rounded-lg focus:border-[#2c5282] focus:ring-1 focus:ring-[#2c5282]"
              >
                <option value="tr">{t('settings.languages.tr')}</option>
                <option value="en">{t('settings.languages.en')}</option>
              </select>
            </div>

            {/* Auto Sync Settings */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-slate-600" />
                  <label className="text-sm font-medium text-slate-700">{t('settings.autoSync')}</label>
                </div>
                <button
                  onClick={() => setSettings({...settings, autoSync: !settings.autoSync})}
                  className={`w-10 h-6 rounded-full transition-colors ${
                    settings.autoSync ? 'bg-[#2c5282]' : 'bg-slate-300'
                  }`}
                >
                  <div className={`w-4 h-4 bg-white rounded-full transition-transform ${
                    settings.autoSync ? 'transform translate-x-5' : 'transform translate-x-1'
                  }`} />
                </button>
              </div>
              
              {settings.autoSync && (
                <select 
                  value={settings.autoSyncInterval}
                  onChange={(e) => setSettings({...settings, autoSyncInterval: parseInt(e.target.value)})}
                  className="w-full p-2 border border-slate-300 rounded-lg focus:border-[#2c5282] focus:ring-1 focus:ring-[#2c5282]"
                >
                  <option value={5}>{t('settings.syncIntervals.5')}</option>
                  <option value={10}>{t('settings.syncIntervals.10')}</option>
                  <option value={15}>{t('settings.syncIntervals.15')}</option>
                </select>
              )}
            </div>

            {/* User Info */}
            <div className="pt-4 border-t space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">{t('settings.user')}:</span>
                <span className="text-slate-800">{user?.email}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">{t('dashboard.totalMails')}:</span>
                <span className="text-slate-800">{storageInfo.totalEmails}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">{t('dashboard.storage')}:</span>
                <span className="text-slate-800">{formatSize(storageInfo.totalSize)}</span>
              </div>
            </div>

            <Button 
              onClick={handleSaveSettings}
              className="w-full h-10 bg-[#2c5282] hover:bg-[#1a365d] text-white rounded-lg"
            >
              <Save className="w-4 h-4 mr-2" />
              {t('common.save')}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Account Connection Modal */}
      <Dialog open={accountConnectOpen} onOpenChange={setAccountConnectOpen}>
        <DialogContent className="sm:max-w-2xl backdrop-blur-md bg-white/95 max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-center text-slate-800 flex items-center justify-center gap-2">
              <Link2 className="w-5 h-5" />
              {t('connect.title')}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-6 pt-4">
            {/* Connected Accounts */}
            {connectedAccounts.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-slate-800">{t('connect.connectedAccounts')}</h3>
                {connectedAccounts.map((account, index) => (
                  <div key={index} className="bg-green-50 border border-green-200 p-4 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <div>
                        <p className="font-medium text-green-800">{account.type} {t('common.email')}</p>
                        <p className="text-sm text-green-600">{account.email}</p>
                        <p className="text-xs text-green-500">{t('connect.connectDate')}: {formatDate(account.connected_at)}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Outlook Multiple Accounts */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg border border-blue-200">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
                  <Mail className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-blue-800">Outlook Hesapları</h3>
                  <p className="text-sm text-blue-600">Microsoft 365 / Exchange / Hotmail - Sınırsız hesap bağlama</p>
                </div>
              </div>
              
              {/* Bağlı Hesaplar Listesi */}
              {connectedAccounts.filter(acc => acc.type === 'Outlook').length > 0 && (
                <div className="mb-4 space-y-2">
                  <h4 className="font-medium text-blue-800 mb-2">Bağlı Hesaplar ({connectedAccounts.filter(acc => acc.type === 'Outlook').length})</h4>
                  {connectedAccounts.filter(acc => acc.type === 'Outlook').map((account) => (
                    <div key={account.id} className="bg-green-100 border border-green-300 p-3 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <CheckCircle className="w-5 h-5 text-green-600" />
                          <div>
                            <p className="font-medium text-green-800">{account.name || account.email.split('@')[0]}</p>
                            <p className="text-sm text-green-700">{account.email}</p>
                          </div>
                        </div>
                        <Button
                          onClick={() => handleDisconnectAccount(account.id, 'Outlook')}
                          variant="outline"
                          size="sm"
                          className="border-red-300 text-red-600 hover:bg-red-50"
                          title="Hesap bağlantısını kes"
                        >
                          <LogOut className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {/* Yeni Hesap Ekleme Formu */}
              <div className="space-y-4">
                <div className="space-y-4 text-sm text-blue-700 mb-4">
                  <p className="text-xs bg-blue-100 p-2 rounded">
                    ⚠️ {t('connect.authWarning')}
                  </p>
                </div>
                
                <div className="space-y-3">
                  <input
                    type="email"
                    placeholder="ornek@outlook.com veya ornek@hotmail.com"
                    value={newOutlookEmail}
                    onChange={(e) => setNewOutlookEmail(e.target.value)}
                    className="w-full px-3 py-2 border border-blue-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <input
                    type="text"
                    placeholder="İsim Soyisim (opsiyonel)"
                    value={newOutlookName}
                    onChange={(e) => setNewOutlookName(e.target.value)}
                    className="w-full px-3 py-2 border border-blue-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <Button 
                  onClick={async () => {
                    const success = await handleConnectOutlook(newOutlookEmail, newOutlookName);
                    if (success) {
                      setNewOutlookEmail('');
                      setNewOutlookName('');
                    }
                  }}
                  disabled={loading || !newOutlookEmail}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Outlook Hesabı Ekle
                </Button>
              </div>
            </div>

            {/* Gmail kısmı kaldırıldı - sadece Outlook desteği */}
          </div>
        </DialogContent>
      </Dialog>

      {/* Import Modal */}
      <Dialog open={importOpen} onOpenChange={setImportOpen}>
        <DialogContent className="sm:max-w-md backdrop-blur-md bg-white/95">
          <DialogHeader>
            <DialogTitle className="text-center text-slate-800">{t('dashboard.import')} {t('common.email')}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            <p className="text-sm text-slate-600 text-center">
              .pst, .ost {language === 'tr' ? 've' : 'or'} .eml {language === 'tr' ? 'dosyalarını seçin' : 'files'}
            </p>
            <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center hover:border-[#2c5282] transition-colors">
              <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
              <input
                type="file"
                accept=".pst,.ost,.eml"
                onChange={(e) => handleImport(e.target.files[0])}
                className="w-full"
                disabled={loading}
              />
            </div>
            {loading && (
              <div className="flex items-center justify-center py-4">
                <RefreshCw className="w-6 h-6 animate-spin text-[#2c5282] mr-2" />
                <span className="text-slate-600">{t('common.loading')}</span>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Export Modal */}
      <Dialog open={exportOpen} onOpenChange={setExportOpen}>
        <DialogContent className="sm:max-w-md backdrop-blur-md bg-white/95">
          <DialogHeader>
            <DialogTitle className="text-center text-slate-800">{t('dashboard.export')} {t('common.email')}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            <p className="text-sm text-slate-600 text-center">
              "{folders[selectedFolder]?.name}" {language === 'tr' ? 'klasörü için dışa aktarma formatını seçin' : 'folder export format'}
            </p>
            <div className="space-y-2">
              <Button 
                onClick={() => handleExport('zip')}
                disabled={loading}
                className="w-full h-12 bg-[#2c5282] hover:bg-[#1a365d] text-white rounded-lg flex items-center justify-center"
              >
                <FileText className="w-4 h-4 mr-2" />
                ZIP Format (.zip)
              </Button>
              <Button 
                onClick={() => handleExport('eml')}
                disabled={loading}
                variant="outline"
                className="w-full h-12 border-slate-300 hover:bg-slate-100 rounded-lg"
              >
                <FileText className="w-4 h-4 mr-2" />
                EML Format (.eml)
              </Button>
              <Button 
                onClick={() => handleExport('json')}
                disabled={loading}
                variant="outline"
                className="w-full h-12 border-slate-300 hover:bg-slate-100 rounded-lg"
              >
                <FileText className="w-4 h-4 mr-2" />
                JSON Format (.json)
              </Button>
            </div>
            {loading && (
              <div className="flex items-center justify-center py-4">
                <RefreshCw className="w-6 h-6 animate-spin text-[#2c5282] mr-2" />
                <span className="text-slate-600">{t('common.loading')}</span>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Dashboard;