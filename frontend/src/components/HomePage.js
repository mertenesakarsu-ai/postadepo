import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { useLanguage } from '../contexts/LanguageContext';
import LanguageSwitcher from './LanguageSwitcher';
import { 
  Shield, 
  Database, 
  DollarSign, 
  Zap, 
  HeadphonesIcon, 
  RefreshCw,
  ArrowRight,
  Mail,
  Server,
  Users
} from 'lucide-react';

const HomePage = () => {
  const { t } = useLanguage();
  const navigate = useNavigate();

  const features = [
    {
      icon: Database,
      title: t('homepage.features.bigData.title'),
      description: t('homepage.features.bigData.description'),
      color: 'text-blue-600'
    },
    {
      icon: DollarSign,
      title: t('homepage.features.affordablePrice.title'),
      description: t('homepage.features.affordablePrice.description'),
      color: 'text-green-600'
    },
    {
      icon: Shield,
      title: t('homepage.features.security.title'),
      description: t('homepage.features.security.description'),
      color: 'text-red-600'
    },
    {
      icon: Zap,
      title: t('homepage.features.integration.title'),
      description: t('homepage.features.integration.description'),
      color: 'text-yellow-600'
    },
    {
      icon: HeadphonesIcon,
      title: t('homepage.features.support.title'),
      description: t('homepage.features.support.description'),
      color: 'text-purple-600'
    },
    {
      icon: RefreshCw,
      title: t('homepage.features.backup.title'),
      description: t('homepage.features.backup.description'),
      color: 'text-indigo-600'
    }
  ];

  const handleGetStarted = () => {
    navigate('/login');
  };

  const handleTryDemo = () => {
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
      {/* Header */}
      <header className="relative z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center space-x-3">
              <img 
                src="https://i.hizliresim.com/9a0rpdc.png" 
                alt="PostaDepo"
                className="h-12 w-auto"
              />
              <div>
                <h1 className="text-xl font-bold text-slate-800">{t('homepage.title')}</h1>
                <p className="text-sm text-slate-600">{t('homepage.subtitle')}</p>
              </div>
            </div>
            
            {/* Language Switcher */}
            <LanguageSwitcher />
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-6xl text-center">
          <div className="mb-8">
            <h1 className="text-5xl md:text-6xl font-bold text-slate-800 mb-6">
              {t('homepage.heroTitle')}
            </h1>
            <p className="text-xl md:text-2xl text-slate-600 mb-8 max-w-4xl mx-auto">
              {t('homepage.heroSubtitle')}
            </p>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
            <Button 
              onClick={handleGetStarted}
              className="bg-[#2c5282] hover:bg-[#1a365d] text-white px-8 py-4 text-lg font-semibold rounded-lg shadow-lg transition-all duration-200 transform hover:scale-105"
            >
              {t('homepage.getStarted')}
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            <Button 
              onClick={handleTryDemo}
              variant="outline"
              className="border-[#2c5282] text-[#2c5282] hover:bg-[#2c5282] hover:text-white px-8 py-4 text-lg font-semibold rounded-lg transition-all duration-200"
            >
              {t('homepage.tryDemo')}
            </Button>
          </div>

          {/* Hero Visual */}
          <div className="relative">
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-2xl p-8 max-w-4xl mx-auto">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
                <div className="flex flex-col items-center">
                  <Mail className="h-12 w-12 text-[#2c5282] mb-3" />
                  <h3 className="text-lg font-semibold text-slate-800">Outlook Integration</h3>
                  <p className="text-slate-600">Microsoft 365 & Exchange</p>
                </div>
                <div className="flex flex-col items-center">
                  <Server className="h-12 w-12 text-[#2c5282] mb-3" />
                  <h3 className="text-lg font-semibold text-slate-800">Secure Backup</h3>
                  <p className="text-slate-600">256-bit Encryption</p>
                </div>
                <div className="flex flex-col items-center">
                  <Users className="h-12 w-12 text-[#2c5282] mb-3" />
                  <h3 className="text-lg font-semibold text-slate-800">Enterprise Ready</h3>
                  <p className="text-slate-600">Scalable Solutions</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4 bg-white/50">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-800 mb-4">
              {t('homepage.features.title')}
            </h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => {
              const IconComponent = feature.icon;
              return (
                <Card key={index} className="bg-white/80 backdrop-blur-sm border-0 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
                  <CardContent className="p-6">
                    <div className="flex items-center mb-4">
                      <div className={`p-3 rounded-lg bg-slate-50 ${feature.color}`}>
                        <IconComponent className="h-6 w-6" />
                      </div>
                    </div>
                    <h3 className="text-xl font-semibold text-slate-800 mb-3">
                      {feature.title}
                    </h3>
                    <p className="text-slate-600">
                      {feature.description}
                    </p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Pricing Section (Ready for Future) */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-6xl text-center">
          <h2 className="text-4xl font-bold text-slate-800 mb-4">
            {t('homepage.pricing.title')}
          </h2>
          <p className="text-xl text-slate-600 mb-12">
            {t('homepage.pricing.subtitle')}
          </p>
          
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg p-12">
            <div className="text-6xl mb-4">🚀</div>
            <h3 className="text-2xl font-bold text-slate-800 mb-2">
              {t('homepage.pricing.comingSoon')}
            </h3>
            <p className="text-slate-600">
              Şu anda demo sürümümüzü ücretsiz deneyebilirsiniz
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 bg-gradient-to-r from-[#2c5282] to-[#1a365d]">
        <div className="container mx-auto max-w-4xl text-center text-white">
          <h2 className="text-4xl font-bold mb-4">
            {t('homepage.cta.title')}
          </h2>
          <p className="text-xl mb-8 opacity-90">
            {t('homepage.cta.subtitle')}
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6">
              <h3 className="text-xl font-semibold mb-3">
                {t('homepage.cta.title')}
              </h3>
              <p className="mb-4 opacity-90">
                {t('homepage.cta.subtitle')}
              </p>
              <Button 
                onClick={handleTryDemo}
                className="bg-white text-[#2c5282] hover:bg-slate-100 font-semibold px-6 py-3 rounded-lg"
              >
                {t('homepage.tryDemo')}
              </Button>
            </div>
            
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6">
              <h3 className="text-xl font-semibold mb-3">
                {t('homepage.cta.contactTitle')}
              </h3>
              <p className="mb-4 opacity-90">
                {t('homepage.cta.contactSubtitle')}
              </p>
              <Button 
                variant="outline"
                className="border-white text-white hover:bg-white hover:text-[#2c5282] font-semibold px-6 py-3 rounded-lg"
              >
                {t('common.email')}: info@postadepo.com
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 bg-slate-800 text-white">
        <div className="container mx-auto max-w-6xl text-center">
          <div className="flex items-center justify-center mb-4">
            <img 
              src="https://customer-assets.emergentagent.com/job_4338b971-040d-400e-9544-183651a406e5/artifacts/g6inru6i_postadepo_logo_transparent.png" 
              alt="PostaDepo"
              className="h-8 w-auto mr-3"
            />
            <span className="text-xl font-bold">{t('homepage.title')}</span>
          </div>
          <p className="text-slate-400">
            © 2025 PostaDepo. {t('homepage.subtitle')}.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;