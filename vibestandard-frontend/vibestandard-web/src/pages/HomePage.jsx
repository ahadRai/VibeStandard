import { HeroSection } from '../components/home/HeroSection';
import { FeatureCards } from '../components/home/FeatureCards';
import { HowItWorks } from '../components/home/HowItWorks';

export function HomePage() {
  return (
    <>
      <HeroSection />
      <FeatureCards />
      <HowItWorks />
    </>
  );
}
