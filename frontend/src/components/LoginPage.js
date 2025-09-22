import React, { useState, useRef } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { toast } from 'sonner';
import { useLanguage } from '../contexts/LanguageContext';
import { Mail, Lock, Eye, EyeOff, UserPlus } from 'lucide-react';
import axios from 'axios';
import ReCAPTCHA from 'react-google-recaptcha';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LoginPage = ({ onLogin }) => {
  const { t } = useLanguage();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotPasswordOpen, setForgotPasswordOpen] = useState(false);
  const [registerOpen, setRegisterOpen] = useState(false);
  const [registerData, setRegisterData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [isRecaptchaVerified, setIsRecaptchaVerified] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const recaptchaRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error(t('auth.fillAllFields'));
      return;
    }

    setLoading(true);
    const result = await onLogin(email, password);
    
    if (result.success) {
      toast.success(t('auth.loginSuccess'));
    } else {
      toast.error(result.message);
    }
    setLoading(false);
  };

  const handleDemoLogin = () => {
    setEmail('demo@postadepo.com');
    setPassword('demo123');
  };

  const handleForgotPassword = () => {
    if (!forgotEmail) {
      toast.error(t('auth.fillAllFields'));
      return;
    }
    toast.success(t('auth.resetLinkSent'));
    setForgotPasswordOpen(false);
    setForgotEmail('');
  };

  const handleRegister = async () => {
    if (!registerData.name || !registerData.email || !registerData.password || !registerData.confirmPassword) {
      toast.error(t('auth.fillAllFields'));
      return;
    }

    if (registerData.password !== registerData.confirmPassword) {
      toast.error(t('auth.passwordMismatch'));
      return;
    }

    if (registerData.password.length < 6) {
      toast.error(t('auth.passwordTooShort'));
      return;
    }

    try {
      const response = await axios.post(`${API}/auth/register`, {
        name: registerData.name,
        email: registerData.email,
        password: registerData.password
      });
      
      toast.success(t('auth.registerSuccess'));
      setRegisterOpen(false);
      setRegisterData({ name: '', email: '', password: '', confirmPassword: '' });
      setEmail(registerData.email);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo Section */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center mb-4">
            <img 
              src="https://customer-assets.emergentagent.com/job_4338b971-040d-400e-9544-183651a406e5/artifacts/g6inru6i_postadepo_logo_transparent.png" 
              alt="PostaDepo"
              className="h-20 w-auto"
            />
          </div>
          <h1 className="text-4xl font-bold text-[#2c5282] mb-2">PostaDepo</h1>
          <p className="text-slate-600 text-lg">E-posta Yönetim Sistemi</p>
        </div>

        {/* Login Card */}
        <Card className="backdrop-blur-sm bg-white/90 border-0 shadow-2xl">
          <CardHeader className="space-y-1 pb-4">
            <CardTitle className="text-2xl text-center text-slate-800">{t('auth.loginTitle')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <Input
                    type="email"
                    placeholder={t('auth.emailPlaceholder')}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-10 h-12 bg-white/70 border-slate-200 focus:border-[#2c5282] focus:ring-[#2c5282] rounded-lg"
                    required
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <Input
                    type={showPassword ? "text" : "password"}
                    placeholder={t('auth.passwordPlaceholder')}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-10 pr-10 h-12 bg-white/70 border-slate-200 focus:border-[#2c5282] focus:ring-[#2c5282] rounded-lg"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-3 text-slate-400 hover:text-slate-600"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <Button 
                type="submit" 
                className="w-full h-12 bg-[#2c5282] hover:bg-[#1a365d] text-white font-semibold rounded-lg shadow-lg transition-all duration-200 transform hover:scale-[1.02]"
                disabled={loading}
              >
                {loading ? t('common.loading') : t('common.login')}
              </Button>
            </form>

            {/* Demo Login Info */}
            <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm font-medium text-blue-800 mb-2">{t('auth.demoLogin')}:</p>
              <p className="text-sm text-blue-700">{t('common.email')}: demo@postadepo.com</p>
              <p className="text-sm text-blue-700">{t('common.password')}: demo123</p>
              <Button 
                type="button"
                variant="outline"
                onClick={handleDemoLogin}
                className="w-full mt-2 border-blue-300 text-blue-700 hover:bg-blue-100 rounded-lg"
              >
                {t('auth.demoUse')}
              </Button>
            </div>

            {/* Links */}
            <div className="flex flex-col space-y-2 pt-4">
              <Dialog open={forgotPasswordOpen} onOpenChange={setForgotPasswordOpen}>
                <DialogTrigger asChild>
                  <button className="text-sm text-[#2c5282] hover:underline text-center">
                    {t('auth.forgotPassword')}
                  </button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md backdrop-blur-md bg-white/90">
                  <DialogHeader>
                    <DialogTitle className="text-center text-slate-800">{t('auth.forgotPassword')}</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 pt-4">
                    <p className="text-sm text-slate-600 text-center">
                      {t('auth.resetPasswordText')}
                    </p>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                      <Input
                        type="email"
                        placeholder={t('auth.emailPlaceholder')}
                        value={forgotEmail}
                        onChange={(e) => setForgotEmail(e.target.value)}
                        className="pl-10 h-12 bg-white/70 border-slate-200 focus:border-[#2c5282] focus:ring-[#2c5282] rounded-lg"
                      />
                    </div>
                    <Button 
                      onClick={handleForgotPassword}
                      className="w-full h-12 bg-[#2c5282] hover:bg-[#1a365d] text-white rounded-lg"
                    >
                      {t('auth.sendResetLink')}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
              
              <Dialog open={registerOpen} onOpenChange={setRegisterOpen}>
                <DialogTrigger asChild>
                  <button className="text-sm text-slate-600 hover:text-[#2c5282] text-center">
                    {t('auth.noAccount')}
                  </button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md backdrop-blur-md bg-white/90">
                  <DialogHeader>
                    <DialogTitle className="text-center text-slate-800 flex items-center justify-center gap-2">
                      <UserPlus className="w-5 h-5" />
                      {t('auth.registerTitle')}
                    </DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 pt-4">
                    <div className="relative">
                      <Input
                        type="text"
                        placeholder={t('auth.namePlaceholder')}
                        value={registerData.name}
                        onChange={(e) => setRegisterData({...registerData, name: e.target.value})}
                        className="h-12 bg-white/70 border-slate-200 focus:border-[#2c5282] focus:ring-[#2c5282] rounded-lg"
                      />
                    </div>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                      <Input
                        type="email"
                        placeholder={t('auth.emailPlaceholder')}
                        value={registerData.email}
                        onChange={(e) => setRegisterData({...registerData, email: e.target.value})}
                        className="pl-10 h-12 bg-white/70 border-slate-200 focus:border-[#2c5282] focus:ring-[#2c5282] rounded-lg"
                      />
                    </div>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                      <Input
                        type="password"
                        placeholder={t('auth.passwordPlaceholder') + " (min. 6)"}
                        value={registerData.password}
                        onChange={(e) => setRegisterData({...registerData, password: e.target.value})}
                        className="pl-10 h-12 bg-white/70 border-slate-200 focus:border-[#2c5282] focus:ring-[#2c5282] rounded-lg"
                      />
                    </div>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                      <Input
                        type="password"
                        placeholder={t('auth.confirmPasswordPlaceholder')}
                        value={registerData.confirmPassword}
                        onChange={(e) => setRegisterData({...registerData, confirmPassword: e.target.value})}
                        className="pl-10 h-12 bg-white/70 border-slate-200 focus:border-[#2c5282] focus:ring-[#2c5282] rounded-lg"
                      />
                    </div>
                    <Button 
                      onClick={handleRegister}
                      className="w-full h-12 bg-[#2c5282] hover:bg-[#1a365d] text-white rounded-lg"
                    >
                      {t('auth.registerTitle')}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default LoginPage;