import Hero from './Hero.jsx'
import ProductsHighlight from './ProductsHighlight.jsx'
import BenefitsStack from './BenefitsStack.jsx'
import Metrics from './Metrics.jsx'
import Awards from './Awards.jsx'
import CardCarousel from './CardCarousel.jsx'
import PressCarousel from './PressCarousel.jsx'
import PreFooter from './PreFooter.jsx'

export default function Main() {
  return (
    <div className="min-h-11 mt-navBarInnerTopBase md:pt-1 text-balance [&amp;_&gt;_.section-bridge]:block-padding [&amp;_&gt;_.figures-stack]:block-padding">
      <Hero />
      <ProductsHighlight />
      <BenefitsStack />
      <Metrics />
      <Awards />
      <CardCarousel />
      <PressCarousel />
      <PreFooter />
    </div>
  )
}
