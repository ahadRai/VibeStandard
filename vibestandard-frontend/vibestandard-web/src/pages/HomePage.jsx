import { useState } from 'react';
import { HeroSection } from '../components/home/HeroSection';
import { FeatureCards } from '../components/home/FeatureCards';
import { HowItWorks } from '../components/home/HowItWorks';
import { ScanResultPanel } from '../components/results/ScanResultPanel';

export function HomePage() {
  const [scanResult, setScanResult] = useState(null);
  const [githubUrl, setGithubUrl] = useState('');

  const handleScanComplete = (result) => {
    setScanResult(result);
  };

  const handleScanStart = (url) => {
    setGithubUrl(url);
  };

  const handleReset = () => {
    setScanResult(null);
    setGithubUrl('');
  };

  if (scanResult) {
    return <ScanResultPanel result={scanResult} onReset={handleReset} githubUrl={githubUrl} />;
  }

  return (
    <>
      <HeroSection onScanComplete={handleScanComplete} onScanStart={handleScanStart} />
      <FeatureCards />
      <HowItWorks />
    </>
  );
}
