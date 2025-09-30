import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { 
  Users, 
  UserCheck, 
  UserX, 
  Database, 
  Shield, 
  CheckCircle, 
  XCircle,
  HardDrive,
  Mail,
  LogOut,
  Settings,
  Search,
  Filter,
  Download,
  UserPlus,
  Trash2,
  Clock,
  Activity
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from './ui/alert-dialog';

const API = `${process.env.REACT_APP_BACKEND_URL}/api` || 'http://localhost:8001/api';

const AdminDashboard = ({ onLogout }) => {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [pendingUsers, setPendingUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all'); // all, approved, pending, admin
  const [systemLogs, setSystemLogs] = useState([]);
  const [bulkActionLoading, setBulkActionLoading] = useState(false);
  const [autoApproval, setAutoApproval] = useState(false);
  const [stats, setStats] = useState({
    totalUsers: 0,
    approvedUsers: 0,
    pendingUsers: 0,
    totalStorage: 0,
    totalEmails: 0
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const token = localStorage.getItem('token');
      console.log('ADMIN DEBUG - Token exists:', !!token);
      console.log('ADMIN DEBUG - API URL:', API);
      
      if (!token) {
        console.log('ADMIN DEBUG - No token, redirecting to login');
        navigate('/login');
        return;
      }

      // Tüm kullanıcıları yükle
      console.log('ADMIN DEBUG - Loading users from:', `${API}/admin/users`);
      const usersResponse = await axios.post(`${API}/admin/users`, {}, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 10000 // 10 saniye timeout
      });
      console.log('ADMIN DEBUG - Users loaded:', usersResponse.data.users?.length);
      setUsers(usersResponse.data.users);

      // Pending kullanıcıları yükle
      console.log('ADMIN DEBUG - Loading pending users from:', `${API}/admin/pending-users`);
      const pendingResponse = await axios.post(`${API}/admin/pending-users`, {}, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 10000 // 10 saniye timeout
      });
      console.log('ADMIN DEBUG - Pending users loaded:', pendingResponse.data.pending_users?.length);
      setPendingUsers(pendingResponse.data.pending_users);

      // Sistem loglarını yükle
      try {
        console.log('ADMIN DEBUG - Loading system logs from:', `${API}/admin/system-logs`);
        const logsResponse = await axios.post(`${API}/admin/system-logs`, {}, {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 10000 // 10 saniye timeout
        });
        console.log('ADMIN DEBUG - System logs loaded:', logsResponse.data.logs?.length);
        setSystemLogs(logsResponse.data.logs);
      } catch (error) {
        console.error('ADMIN DEBUG - System logs load error:', error);
        // Log loading hatası kritik değil, devam et
      }

      // İstatistikleri hesapla
      calculateStats(usersResponse.data.users, pendingResponse.data.pending_users);
      
      // Admin ayarlarını yükle
      try {
        console.log('ADMIN DEBUG - Loading admin settings from:', `${API}/admin/settings/get`);
        const settingsResponse = await axios.post(`${API}/admin/settings/get`, {}, {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 10000 // 10 saniye timeout
        });
        console.log('ADMIN DEBUG - Admin settings loaded:', settingsResponse.data.settings);
        setAutoApproval(settingsResponse.data.settings.auto_approval);
      } catch (error) {
        console.error('ADMIN DEBUG - Admin settings load error:', error);
        // Settings loading hatası kritik değil, default false kullan
        setAutoApproval(false);
      }
      
      console.log('ADMIN DEBUG - Data loading completed successfully');

    } catch (error) {
      console.error('ADMIN DEBUG - Data load error:', error);
      console.error('ADMIN DEBUG - Error details:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        url: error.config?.url
      });
      
      if (error.response?.status === 403) {
        toast.error('Admin yetkisi gerekli');
        navigate('/dashboard');
      } else if (error.response?.status === 401) {
        toast.error('Oturum süresi dolmuş');
        localStorage.removeItem('token');
        navigate('/login');
      } else {
        toast.error('Veriler yüklenirken hata oluştu');
        console.error('ADMIN DEBUG - Staying on admin page despite error for debugging');
        // Don't navigate away so we can see the error
      }
    } finally {
      setLoading(false);
      console.log('ADMIN DEBUG - Loading state set to false');
    }
  };

  const calculateStats = (allUsers, pendingUsersList) => {
    const approvedUsers = allUsers.filter(user => user.approved);
    const totalStorage = allUsers.reduce((sum, user) => sum + (user.storage_info?.totalSize || 0), 0);
    const totalEmails = allUsers.reduce((sum, user) => sum + (user.storage_info?.totalEmails || 0), 0);

    setStats({
      totalUsers: allUsers.length,
      approvedUsers: approvedUsers.length,
      pendingUsers: pendingUsersList.length,
      totalStorage,
      totalEmails
    });
  };

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleApproveUser = async (userId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/approve-user/${userId}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Kullanıcı başarıyla onaylandı');
      loadData(); // Verileri yeniden yükle
    } catch (error) {
      console.error('Approve error:', error);
      toast.error('Kullanıcı onaylanırken hata oluştu');
    }
  };

  const handleRejectUser = async (userId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/reject-user/${userId}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Kullanıcı reddedildi ve hesabı silindi');
      loadData(); // Verileri yeniden yükle
    } catch (error) {
      console.error('Reject error:', error);
      toast.error('Kullanıcı reddedilirken hata oluştu');
    }
  };

  const handleLogout = async () => {
    try {
      console.log('Admin panelinden çıkış işlemi başlıyor...');
      
      // Loading state göster
      setLoading(true);
      
      // LocalStorage'ı temizle ve global state'i güncelle
      if (onLogout) {
        onLogout(); // Global App.js logout fonksiyonunu çağır
      } else {
        // Fallback - manuel olarak temizle
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
      
      console.log('LocalStorage temizlendi ve global state güncellendi');
      
      // Başarı mesajı göster
      toast.success('Admin panelinden başarıyla çıkış yapıldı');
      
      console.log('Login sayfasına yönlendiriliyor...');
      
      // Hemen yönlendir
      navigate('/login', { replace: true });
      
    } catch (error) {
      console.error('Admin panel logout error:', error);
      toast.error('Çıkış işlemi sırasında hata oluştu');
      
      // Hata olsa da çıkış yap
      if (onLogout) {
        onLogout();
      } else {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
      navigate('/login', { replace: true });
    } finally {
      // Loading state'i her durumda false yap
      setLoading(false);
    }
  };

  const handleBulkApprove = async () => {
    try {
      setBulkActionLoading(true);
      const token = localStorage.getItem('token');
      
      // Tüm pending kullanıcıların ID'lerini al
      const userIds = pendingUsers.map(user => user.id);
      
      if (userIds.length === 0) {
        toast.error('Onaylanacak kullanıcı bulunamadı');
        return;
      }
      
      const response = await axios.post(`${API}/admin/bulk-approve-users`, {
        user_ids: userIds
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success(response.data.message);
      loadData(); // Verileri yeniden yükle
    } catch (error) {
      console.error('Bulk approve error:', error);
      toast.error(error.response?.data?.detail || 'Toplu onaylama sırasında hata oluştu');
    } finally {
      setBulkActionLoading(false);
    }
  };

  const handleBulkReject = async () => {
    try {
      setBulkActionLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await axios.post(`${API}/admin/bulk-reject-users`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success(response.data.message);
      loadData(); // Verileri yeniden yükle
    } catch (error) {
      console.error('Bulk reject error:', error);
      toast.error('Toplu reddetme sırasında hata oluştu');
    } finally {
      setBulkActionLoading(false);
    }
  };

  const handleExportLogs = async () => {
    try {
      const token = localStorage.getItem('token');
      
      const response = await axios.post(`${API}/admin/system-logs/export`, {}, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      // Dosya indirme
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `sistem_loglari_${new Date().toISOString().slice(0,10)}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Sistem logları başarıyla indirildi');
    } catch (error) {
      console.error('Export logs error:', error);
      toast.error('Log indirme sırasında hata oluştu');
    }
  };

  const handleToggleAutoApproval = async () => {
    try {
      const newValue = !autoApproval;
      const token = localStorage.getItem('token');
      
      console.log('ADMIN DEBUG - Updating auto approval setting:', newValue);
      const response = await axios.post(`${API}/admin/settings/update`, 
        { auto_approval: newValue }, 
        { 
          headers: { Authorization: `Bearer ${token}` },
          timeout: 10000 // 10 saniye timeout
        }
      );
      
      console.log('ADMIN DEBUG - Auto approval updated:', response.data);
      setAutoApproval(newValue);
      toast.success(response.data.message || (newValue ? 'Otomatik onay açıldı' : 'Otomatik onay kapatıldı'));
    } catch (error) {
      console.error('ADMIN DEBUG - Auto approval update error:', error);
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        toast.error('İstek zaman aşımına uğradı. Lütfen tekrar deneyin.');
      } else {
        toast.error('Otomatik onay ayarı güncellenirken hata oluştu');
      }
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (filterType === 'approved') return matchesSearch && user.approved;
    if (filterType === 'pending') return matchesSearch && !user.approved;
    if (filterType === 'admin') return matchesSearch && user.user_type === 'admin';
    
    return matchesSearch;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center">
          <Database className="w-12 h-12 text-slate-600 animate-spin mx-auto mb-4" />
          <p className="text-slate-600">Admin paneli yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <Shield className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Admin Panel</h1>
                <p className="text-sm text-slate-600">PostaDepo Yönetim Sistemi</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                onClick={handleLogout}
                disabled={loading}
                className="text-red-600 hover:text-red-700 disabled:opacity-50"
              >
                <LogOut className="w-4 h-4 mr-2" />
                {loading ? 'Çıkış Yapılıyor...' : 'Çıkış Yap'}
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Toplam Kullanıcı</CardTitle>
              <Users className="w-4 h-4 text-slate-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-slate-900">{stats.totalUsers}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Onaylı Hesaplar</CardTitle>
              <UserCheck className="w-4 h-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{stats.approvedUsers}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Bekleyen Onay</CardTitle>
              <UserX className="w-4 h-4 text-orange-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">{stats.pendingUsers}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Toplam E-posta</CardTitle>
              <Mail className="w-4 h-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">{stats.totalEmails}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Toplam Depolama</CardTitle>
              <HardDrive className="w-4 h-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-purple-600">{formatSize(stats.totalStorage)}</div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="users" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="users">Tüm Kullanıcılar</TabsTrigger>
            <TabsTrigger value="pending">Onay Bekleyenler ({stats.pendingUsers})</TabsTrigger>
            <TabsTrigger value="system">Sistem</TabsTrigger>
          </TabsList>

          <TabsContent value="users" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle>Kullanıcı Yönetimi</CardTitle>
                    <CardDescription>Tüm kullanıcıları görüntüleyin ve yönetin</CardDescription>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="relative">
                      <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
                      <Input
                        placeholder="Kullanıcı ara..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10 w-64"
                      />
                    </div>
                    <select
                      value={filterType}
                      onChange={(e) => setFilterType(e.target.value)}
                      className="px-3 py-2 border rounded-md bg-white text-sm"
                    >
                      <option value="all">Tümü</option>
                      <option value="approved">Onaylı</option>
                      <option value="pending">Bekleyen</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Kullanıcı</TableHead>
                      <TableHead>E-posta</TableHead>
                      <TableHead>Durum</TableHead>
                      <TableHead>Tip</TableHead>
                      <TableHead>E-posta Sayısı</TableHead>
                      <TableHead>Depolama</TableHead>
                      <TableHead>İşlemler</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredUsers.map((user) => (
                      <TableRow key={user.id}>
                        <TableCell className="font-medium">{user.name}</TableCell>
                        <TableCell>{user.email}</TableCell>
                        <TableCell>
                          {user.approved ? (
                            <Badge variant="default" className="bg-green-100 text-green-800">
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Onaylı
                            </Badge>
                          ) : (
                            <Badge variant="secondary" className="bg-orange-100 text-orange-800">
                              <XCircle className="w-3 h-3 mr-1" />
                              Bekleyen
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge variant={user.user_type === 'admin' ? 'destructive' : 'outline'}>
                            {user.user_type === 'admin' ? 'Admin' : user.user_type}
                          </Badge>
                        </TableCell>
                        <TableCell>{user.storage_info?.totalEmails || 0}</TableCell>
                        <TableCell>{formatSize(user.storage_info?.totalSize || 0)}</TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            {!user.approved && (
                              <>
                                <Button
                                  size="sm"
                                  onClick={() => handleApproveUser(user.id)}
                                  className="bg-green-600 hover:bg-green-700 text-white"
                                >
                                  <CheckCircle className="w-3 h-3 mr-1" />
                                  Onayla
                                </Button>
                                <AlertDialog>
                                  <AlertDialogTrigger asChild>
                                    <Button
                                      size="sm"
                                      variant="destructive"
                                    >
                                      <XCircle className="w-3 h-3 mr-1" />
                                      Reddet
                                    </Button>
                                  </AlertDialogTrigger>
                                  <AlertDialogContent>
                                    <AlertDialogHeader>
                                      <AlertDialogTitle>Kullanıcıyı Reddet</AlertDialogTitle>
                                      <AlertDialogDescription>
                                        Bu işlem {user.email} kullanıcısını reddedecek ve hesabını tamamen silecektir. 
                                        Bu işlem geri alınamaz.
                                      </AlertDialogDescription>
                                    </AlertDialogHeader>
                                    <AlertDialogFooter>
                                      <AlertDialogCancel>İptal</AlertDialogCancel>
                                      <AlertDialogAction
                                        onClick={() => handleRejectUser(user.id)}
                                        className="bg-red-600 hover:bg-red-700"
                                      >
                                        Reddet ve Sil
                                      </AlertDialogAction>
                                    </AlertDialogFooter>
                                  </AlertDialogContent>
                                </AlertDialog>
                              </>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="pending" className="space-y-6">
            {/* Otomatik Kayıt Onayı Ayarı */}
            <Card>
              <CardHeader>
                <CardTitle>Otomatik Kayıt Onayı</CardTitle>
                <CardDescription>Yeni kullanıcıların otomatik olarak onaylanmasını ayarlayın</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <p className="font-medium">Otomatik Onay</p>
                    <p className="text-sm text-slate-600">Yeni kullanıcıları otomatik onayla</p>
                  </div>
                  <div 
                    className={`w-12 h-6 ${autoApproval ? 'bg-blue-500' : 'bg-slate-200'} rounded-full relative cursor-pointer transition-colors`}
                    onClick={handleToggleAutoApproval}
                  >
                    <div className={`w-4 h-4 bg-white rounded-full absolute top-1 ${autoApproval ? 'right-1' : 'left-1'} shadow transition-all`}></div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Toplu İşlemler */}
            {pendingUsers.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Toplu İşlemler</CardTitle>
                  <CardDescription>Tüm bekleyen kullanıcıları toplu işlemlerle yönetin</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center space-x-4">
                    <Button 
                      onClick={handleBulkApprove}
                      disabled={bulkActionLoading}
                      className="bg-green-600 hover:bg-green-700 text-white"
                    >
                      <UserPlus className="w-4 h-4 mr-2" />
                      {bulkActionLoading ? 'İşleniyor...' : `Tüm Bekleyen Kullanıcıları Onayla (${pendingUsers.length})`}
                    </Button>
                    
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button 
                          variant="destructive"
                          disabled={bulkActionLoading}
                        >
                          <Trash2 className="w-4 h-4 mr-2" />
                          Tüm Bekleyen Kullanıcıları Reddet
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Toplu Kullanıcı Reddi</AlertDialogTitle>
                          <AlertDialogDescription>
                            Bu işlem {pendingUsers.length} bekleyen kullanıcıyı reddedecek ve hesaplarını tamamen silecektir. 
                            Bu işlem geri alınamaz.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>İptal</AlertDialogCancel>
                          <AlertDialogAction
                            onClick={handleBulkReject}
                            className="bg-red-600 hover:bg-red-700"
                          >
                            {bulkActionLoading ? 'İşleniyor...' : 'Tümünü Reddet ve Sil'}
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Onay Bekleyen Kullanıcılar Tablosu */}
            <Card>
              <CardHeader>
                <CardTitle>Onay Bekleyen Kullanıcılar</CardTitle>
                <CardDescription>Admin onayı bekleyen yeni kayıtları yönetin</CardDescription>
              </CardHeader>
              <CardContent>
                {pendingUsers.length === 0 ? (
                  <div className="text-center py-8">
                    <UserCheck className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                    <p className="text-slate-600">Onay bekleyen kullanıcı bulunmuyor</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>İsim</TableHead>
                        <TableHead>E-posta</TableHead>
                        <TableHead>Kayıt Tarihi</TableHead>
                        <TableHead>İşlemler</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {pendingUsers.map((user) => (
                        <TableRow key={user.id}>
                          <TableCell className="font-medium">{user.name}</TableCell>
                          <TableCell>{user.email}</TableCell>
                          <TableCell>
                            {user.created_at ? new Date(user.created_at).toLocaleDateString('tr-TR') : '-'}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center space-x-2">
                              <Button
                                size="sm"
                                onClick={() => handleApproveUser(user.id)}
                                className="bg-green-600 hover:bg-green-700 text-white"
                              >
                                <CheckCircle className="w-3 h-3 mr-1" />
                                Onayla
                              </Button>
                              <AlertDialog>
                                <AlertDialogTrigger asChild>
                                  <Button
                                    size="sm"
                                    variant="destructive"
                                  >
                                    <XCircle className="w-3 h-3 mr-1" />
                                    Reddet
                                  </Button>
                                </AlertDialogTrigger>
                                <AlertDialogContent>
                                  <AlertDialogHeader>
                                    <AlertDialogTitle>Kullanıcıyı Reddet</AlertDialogTitle>
                                    <AlertDialogDescription>
                                      Bu işlem {user.email} kullanıcısını reddedecek ve hesabını tamamen silecektir. 
                                      Bu işlem geri alınamaz.
                                    </AlertDialogDescription>
                                  </AlertDialogHeader>
                                  <AlertDialogFooter>
                                    <AlertDialogCancel>İptal</AlertDialogCancel>
                                    <AlertDialogAction
                                      onClick={() => handleRejectUser(user.id)}
                                      className="bg-red-600 hover:bg-red-700"
                                    >
                                      Reddet ve Sil
                                    </AlertDialogAction>
                                  </AlertDialogFooter>
                                </AlertDialogContent>
                              </AlertDialog>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="system" className="space-y-6">
            {/* Sistem Performansı - Analitikler'den taşındı */}
            <Card>
              <CardHeader>
                <CardTitle>Sistem Performansı</CardTitle>
                <CardDescription>Platform sağlık durumu ve performans metrikleri</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">Server Durumu</span>
                      <Badge className="bg-green-100 text-green-800">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        Çevrimiçi
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">Veritabanı</span>
                      <Badge className="bg-green-100 text-green-800">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        Bağlı
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">E-posta Servisi</span>
                      <Badge className="bg-green-100 text-green-800">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        Aktif
                      </Badge>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">Toplam Depolama</span>
                      <span className="text-sm text-slate-600">{formatSize(stats.totalStorage)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">Aktif Kullanıcı</span>
                      <span className="text-sm text-slate-600">{stats.approvedUsers}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">Toplam E-posta</span>
                      <span className="text-sm text-slate-600">{stats.totalEmails}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Sistem Logları */}
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle>Sistem Logları</CardTitle>
                    <CardDescription>Son sistem aktiviteleri ve işlem kayıtları</CardDescription>
                  </div>
                  <Button 
                    variant="outline" 
                    onClick={handleExportLogs}
                    className="border-blue-200 hover:bg-blue-50"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Sistem Log Yedekle
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {systemLogs.length > 0 ? systemLogs.map((log) => (
                    <div key={log.id} className="flex items-start space-x-3 p-3 border rounded-lg">
                      <div className="flex-shrink-0">
                        {log.log_type === 'USER_REGISTER' && <UserPlus className="w-4 h-4 text-blue-500" />}
                        {log.log_type === 'USER_LOGIN' && <CheckCircle className="w-4 h-4 text-green-500" />}
                        {log.log_type === 'USER_APPROVED' && <UserCheck className="w-4 h-4 text-green-500" />}
                        {log.log_type === 'EMAIL_ACCOUNT_CONNECTED' && <Mail className="w-4 h-4 text-purple-500" />}
                        {log.log_type === 'BULK_USER_APPROVED' && <UserPlus className="w-4 h-4 text-green-500" />}
                        {log.log_type === 'BULK_USER_REJECTED' && <Trash2 className="w-4 h-4 text-red-500" />}
                        {!['USER_REGISTER', 'USER_LOGIN', 'USER_APPROVED', 'EMAIL_ACCOUNT_CONNECTED', 'BULK_USER_APPROVED', 'BULK_USER_REJECTED'].includes(log.log_type) && <Activity className="w-4 h-4 text-gray-500" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline" className="text-xs">
                            {log.log_type.replace(/_/g, ' ')}
                          </Badge>
                          <span className="text-xs text-slate-500">
                            <Clock className="w-3 h-3 inline mr-1" />
                            {log.formatted_timestamp || new Date(log.timestamp).toLocaleString('tr-TR')}
                          </span>
                        </div>
                        <p className="text-sm mt-1">{log.message}</p>
                        {log.user_email && (
                          <p className="text-xs text-slate-500 mt-1">Kullanıcı: {log.user_email}</p>
                        )}
                      </div>
                    </div>
                  )) : (
                    <div className="text-center py-8">
                      <Activity className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                      <p className="text-slate-600">Henüz sistem logu bulunmuyor</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default AdminDashboard;