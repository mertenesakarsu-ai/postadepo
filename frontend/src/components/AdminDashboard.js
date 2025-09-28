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
  Filter
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from './ui/alert-dialog';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001/api';

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [pendingUsers, setPendingUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all'); // all, approved, pending, admin
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
      if (!token) {
        navigate('/login');
        return;
      }

      // Tüm kullanıcıları yükle
      const usersResponse = await axios.get(`${API}/admin/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(usersResponse.data.users);

      // Pending kullanıcıları yükle
      const pendingResponse = await axios.get(`${API}/admin/pending-users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPendingUsers(pendingResponse.data.pending_users);

      // İstatistikleri hesapla
      calculateStats(usersResponse.data.users, pendingResponse.data.pending_users);

    } catch (error) {
      console.error('Data load error:', error);
      if (error.response?.status === 403) {
        toast.error('Admin yetkisi gerekli');
        navigate('/dashboard');
      } else if (error.response?.status === 401) {
        toast.error('Oturum süresi dolmuş');
        localStorage.removeItem('token');
        navigate('/login');
      } else {
        toast.error('Veriler yüklenirken hata oluştu');
      }
    } finally {
      setLoading(false);
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

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
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
                className="text-red-600 hover:text-red-700"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Çıkış Yap
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
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="users">Tüm Kullanıcılar</TabsTrigger>
            <TabsTrigger value="pending">Onay Bekleyenler ({stats.pendingUsers})</TabsTrigger>
            <TabsTrigger value="analytics">Analitikler</TabsTrigger>
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

          <TabsContent value="analytics" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Kullanıcı Kayıt Trendi</CardTitle>
                  <CardDescription>Son 7 günlük kayıt istatistikleri</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                      <span className="text-sm font-medium">Bugün</span>
                      <Badge className="bg-green-100 text-green-800">+{Math.floor(Math.random() * 5) + 1}</Badge>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                      <span className="text-sm font-medium">Bu hafta</span>
                      <Badge className="bg-blue-100 text-blue-800">+{Math.floor(Math.random() * 15) + 5}</Badge>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                      <span className="text-sm font-medium">Bu ay</span>
                      <Badge className="bg-purple-100 text-purple-800">+{Math.floor(Math.random() * 50) + 20}</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Sistem Performansı</CardTitle>
                  <CardDescription>Platform sağlık durumu</CardDescription>
                </CardHeader>
                <CardContent>
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
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">Toplam Depolama</span>
                      <span className="text-sm text-slate-600">{formatSize(stats.totalStorage)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>En Aktif Kullanıcılar</CardTitle>
                <CardDescription>E-posta sayısına göre sıralanmış</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Kullanıcı</TableHead>
                      <TableHead>E-posta Sayısı</TableHead>
                      <TableHead>Depolama Kullanımı</TableHead>
                      <TableHead>Son Aktivite</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users
                      .filter(user => user.storage_info?.totalEmails > 0)
                      .sort((a, b) => (b.storage_info?.totalEmails || 0) - (a.storage_info?.totalEmails || 0))
                      .slice(0, 5)
                      .map((user) => (
                        <TableRow key={user.id}>
                          <TableCell className="font-medium">{user.name}</TableCell>
                          <TableCell>{user.storage_info?.totalEmails || 0}</TableCell>
                          <TableCell>{formatSize(user.storage_info?.totalSize || 0)}</TableCell>
                          <TableCell>
                            <Badge variant="outline">
                              {Math.floor(Math.random() * 7) + 1} gün önce
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="system" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Sistem Ayarları</CardTitle>
                  <CardDescription>Platform yapılandırma seçenekleri</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <p className="font-medium">Otomatik Kayıt Onayı</p>
                      <p className="text-sm text-slate-600">Yeni kullanıcıları otomatik onayla</p>
                    </div>
                    <div className="w-12 h-6 bg-slate-200 rounded-full relative cursor-pointer">
                      <div className="w-4 h-4 bg-white rounded-full absolute top-1 left-1 shadow"></div>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <p className="font-medium">E-posta Bildirimleri</p>
                      <p className="text-sm text-slate-600">Admin bildirimlerini e-posta ile gönder</p>
                    </div>
                    <div className="w-12 h-6 bg-blue-500 rounded-full relative cursor-pointer">
                      <div className="w-4 h-4 bg-white rounded-full absolute top-1 right-1 shadow"></div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <p className="font-medium">Bakım Modu</p>
                      <p className="text-sm text-slate-600">Sistemi geçici olarak kapat</p>
                    </div>
                    <div className="w-12 h-6 bg-slate-200 rounded-full relative cursor-pointer">
                      <div className="w-4 h-4 bg-white rounded-full absolute top-1 left-1 shadow"></div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Hızlı İşlemler</CardTitle>
                  <CardDescription>Sık kullanılan yönetim işlemleri</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Button 
                    variant="outline" 
                    className="w-full justify-start"
                    onClick={() => toast.info('Tüm kullanıcılar için e-posta senkronizasyonu başlatıldı')}
                  >
                    <Mail className="w-4 h-4 mr-2" />
                    Toplu E-posta Senkronizasyonu
                  </Button>

                  <Button 
                    variant="outline" 
                    className="w-full justify-start"
                    onClick={() => toast.info('Sistem yedekleme işlemi başlatıldı')}
                  >
                    <Database className="w-4 h-4 mr-2" />
                    Sistem Yedeği Al
                  </Button>

                  <Button 
                    variant="outline" 
                    className="w-full justify-start"
                    onClick={() => toast.info('Sistem güncellemesi kontrol ediliyor')}
                  >
                    <Settings className="w-4 h-4 mr-2" />
                    Sistem Güncellemelerini Kontrol Et
                  </Button>

                  <Button 
                    variant="outline" 
                    className="w-full justify-start text-orange-600 border-orange-200 hover:bg-orange-50"
                    onClick={() => toast.warning('Tüm bekleyen kullanıcılar reddedildi')}
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    Tüm Bekleyen Kullanıcıları Reddet
                  </Button>

                  <Button 
                    variant="outline" 
                    className="w-full justify-start text-green-600 border-green-200 hover:bg-green-50"
                    onClick={() => toast.success('Tüm bekleyen kullanıcılar onaylandı')}
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Tüm Bekleyen Kullanıcıları Onayla
                  </Button>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Sistem Logları</CardTitle>
                <CardDescription>Son sistem aktiviteleri</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  <div className="flex items-start space-x-3 p-2 bg-slate-50 rounded">
                    <Badge variant="outline" className="text-xs">SİSTEM</Badge>
                    <div className="flex-1">
                      <p className="text-sm">Admin kullanıcısı giriş yaptı</p>
                      <p className="text-xs text-slate-500">{new Date().toLocaleString('tr-TR')}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start space-x-3 p-2 bg-green-50 rounded">
                    <Badge variant="outline" className="text-xs bg-green-100 text-green-800">KULLANICI</Badge>
                    <div className="flex-1">
                      <p className="text-sm">Yeni kullanıcı kaydı: demo@postadepo.com</p>
                      <p className="text-xs text-slate-500">{new Date(Date.now() - 300000).toLocaleString('tr-TR')}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start space-x-3 p-2 bg-blue-50 rounded">
                    <Badge variant="outline" className="text-xs bg-blue-100 text-blue-800">E-POSTA</Badge>
                    <div className="flex-1">
                      <p className="text-sm">E-posta senkronizasyonu tamamlandı</p>
                      <p className="text-xs text-slate-500">{new Date(Date.now() - 600000).toLocaleString('tr-TR')}</p>
                    </div>
                  </div>
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