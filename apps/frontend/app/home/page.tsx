import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from "@/components/ui/accordion";
import { ArrowRight, Sparkles, Zap, Shield, Check, Star, PlayCircle } from "lucide-react";

export default function LandingPage() {
    return (
        <div className="flex flex-col min-h-screen bg-background text-foreground">
            {/* Background decoration */}
            <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
                <div className="absolute top-0 right-1/4 w-[500px] h-[500px] bg-primary/20 rounded-full blur-[100px] opacity-30 animate-pulse" />
                <div className="absolute bottom-0 left-1/4 w-[500px] h-[500px] bg-secondary/20 rounded-full blur-[100px] opacity-30 animate-pulse [animation-delay:2s]" />
            </div>

            {/* Navigation / Header */}
            <header className="sticky top-0 z-50 w-full border-b border-border/50 bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
                <div className="container mx-auto flex h-16 items-center justify-between px-4 md:px-6">
                    <Link href="/home" className="flex items-center gap-2 font-bold text-xl">
                        <span className="bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent">Verbix AI</span>
                    </Link>
                    <nav className="hidden md:flex gap-6 text-sm font-medium text-muted-foreground">
                        <Link href="#features" className="hover:text-primary transition-colors">Features</Link>
                        <Link href="#testimonials" className="hover:text-primary transition-colors">Testimonials</Link>
                        <Link href="#pricing" className="hover:text-primary transition-colors">Pricing</Link>
                        <Link href="#faq" className="hover:text-primary transition-colors">FAQ</Link>
                        <Link href="/developer" className="hover:text-primary transition-colors">Developer</Link>
                    </nav>
                    <div className="flex items-center gap-4">
                        <Link href="/">
                            <Button>Get Started</Button>
                        </Link>
                    </div>
                </div>
            </header>

            <main className="flex-1">
                {/* Hero Section - Vertically Centered */}
                <section className="relative min-h-[calc(100vh-4rem)] flex flex-col justify-center items-center py-20 overflow-hidden">
                    <div className="container mx-auto px-4 md:px-6 relative z-10 text-center space-y-8">
                        <div className="inline-flex items-center justify-center px-4 py-1.5 rounded-full border border-border bg-card/50 backdrop-blur-sm text-sm font-medium text-muted-foreground mb-4 hover:border-primary/50 transition-colors cursor-default animate-fade-in-up">
                            <Sparkles className="w-4 h-4 mr-2 text-yellow-400" />
                            <span>Next-Generation AI Content Creation</span>
                        </div>

                        <h1 className="text-5xl md:text-7xl lg:text-8xl font-black tracking-tighter bg-gradient-to-b from-foreground to-foreground/50 bg-clip-text text-transparent max-w-5xl mx-auto leading-[1.1]">
                            Create Content at the <br className="hidden md:block" /> Speed of Thought
                        </h1>

                        <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
                            Verbix AI combines advanced AI models to help you generate blogs, images, and videos in seconds.
                            Unleash your creativity with the ultimate AI workspace.
                        </p>

                        <div className="flex flex-col sm:flex-row gap-4 justify-center pt-8">
                            <Link href="/">
                                <Button size="lg" className="h-14 px-10 text-lg shadow-xl shadow-primary/20 hover:shadow-primary/40 transition-all rounded-full">
                                    Start Creating for Free <ArrowRight className="ml-2 w-5 h-5" />
                                </Button>
                            </Link>
                            <Link href="#how-it-works">
                                <Button variant="outline" size="lg" className="h-14 px-10 text-lg backdrop-blur-sm bg-card/30 rounded-full border-primary/20 hover:bg-primary/10">
                                    <PlayCircle className="mr-2 w-5 h-5" /> How it Works
                                </Button>
                            </Link>
                        </div>

                        {/* Trusted By Strip */}
                        <div className="pt-20 opacity-60 grayscale hover:grayscale-0 transition-all duration-500">
                            <p className="text-sm font-medium text-muted-foreground mb-6">TRUSTED BY INNOVATORS AT</p>
                            <div className="flex flex-wrap justify-center gap-8 md:gap-16 items-center">
                                {/* Mock Logos - represented by text for now */}
                                <span className="text-xl font-bold font-mono">ACME Corp</span>
                                <span className="text-xl font-bold font-serif">Globex</span>
                                <span className="text-xl font-bold tracking-widest">SOYLENT</span>
                                <span className="text-xl font-bold italic">Initech</span>
                                <span className="text-xl font-bold">Umbrella</span>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Features Section */}
                <section id="features" className="py-24 bg-muted/10">
                    <div className="container mx-auto px-4 md:px-6 space-y-16">
                        <div className="text-center space-y-4 max-w-3xl mx-auto">
                            <h2 className="text-4xl font-bold tracking-tight">Everything You Need</h2>
                            <p className="text-muted-foreground text-xl">
                                A complete suite of AI tools designed to supercharge your workflow.
                            </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                            {[
                                {
                                    icon: Sparkles,
                                    title: "AI Text Generation",
                                    description: "Generate high-quality blog posts, articles, and marketing copy with state-of-the-art language models."
                                },
                                {
                                    icon: Zap,
                                    title: "Instant Image Creation",
                                    description: "Turn text descriptions into breathtaking visuals. Perfect for social media, ads, and web content."
                                },
                                {
                                    icon: Shield,
                                    title: "Secure & Private",
                                    description: "Your data is yours. We prioritize security and privacy, ensuring your content remains confidential."
                                }
                            ].map((feature, i) => (
                                <Card key={i} className="group bg-card/40 border-border/50 backdrop-blur-sm hover:bg-card/60 transition-all hover:-translate-y-1">
                                    <CardHeader>
                                        <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
                                            <feature.icon className="w-7 h-7 text-primary" />
                                        </div>
                                        <CardTitle className="text-2xl">{feature.title}</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <p className="text-muted-foreground text-lg leading-relaxed">
                                            {feature.description}
                                        </p>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    </div>
                </section>

                {/* Testimonials Section */}
                <section id="testimonials" className="py-24">
                    <div className="container mx-auto px-4 md:px-6 space-y-16">
                        <div className="text-center space-y-4 max-w-3xl mx-auto">
                            <h2 className="text-4xl font-bold tracking-tight">Loved by Creators</h2>
                            <p className="text-muted-foreground text-xl">
                                See what the community is saying about Verbix AI.
                            </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {[
                                {
                                    quote: "Verbix AI has completely transformed how I write content. It's like having a team of writers at my fingertips.",
                                    author: "Sarah J.",
                                    role: "Content Marketer"
                                },
                                {
                                    quote: "The image generation quality is unmatched. I use it for all my social media posts now.",
                                    author: "Mike T.",
                                    role: "Digital Artist"
                                },
                                {
                                    quote: "Fast, reliable, and incredibly easy to use. The best AI tool I've tried this year.",
                                    author: "Emily R.",
                                    role: "Startup Founder"
                                }
                            ].map((testimonial, i) => (
                                <Card key={i} className="bg-card/30 border-border/50 backdrop-blur-sm">
                                    <CardContent className="pt-6">
                                        <div className="flex gap-1 mb-4">
                                            {[1, 2, 3, 4, 5].map((star) => (
                                                <Star key={star} className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                                            ))}
                                        </div>
                                        <p className="text-lg italic text-muted-foreground mb-6">"{testimonial.quote}"</p>
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-purple-500 flex items-center justify-center text-primary-foreground font-bold">
                                                {testimonial.author[0]}
                                            </div>
                                            <div>
                                                <p className="font-semibold">{testimonial.author}</p>
                                                <p className="text-xs text-muted-foreground uppercase tracking-wider">{testimonial.role}</p>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    </div>
                </section>

                {/* Pricing Section */}
                <section id="pricing" className="py-24 bg-muted/10">
                    <div className="container mx-auto px-4 md:px-6 space-y-16">
                        <div className="text-center space-y-4 max-w-3xl mx-auto">
                            <h2 className="text-4xl font-bold tracking-tight">Simple, Transparent Pricing</h2>
                            <p className="text-muted-foreground text-xl">
                                Choose the plan that fits your needs. No hidden fees.
                            </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
                            {[
                                {
                                    title: "Free",
                                    price: "$0",
                                    description: "Perfect for getting started.",
                                    features: ["5 AI Generations/day", "Standard Support", "Basic Templates"],
                                    cta: "Start for Free",
                                    variant: "outline"
                                },
                                {
                                    title: "Pro",
                                    price: "$29",
                                    period: "/mo",
                                    description: "For creators who need more power.",
                                    features: ["Unlimited Generations", "Priority Support", "Advanced Templates", "Higher Resolution Images"],
                                    cta: "Get Pro",
                                    variant: "default",
                                    popular: true
                                },
                                {
                                    title: "Enterprise",
                                    price: "Custom",
                                    description: "For teams and organizations.",
                                    features: ["Custom API Access", "Dedicated Account Manager", "SSO & Security", "Custom Model Fine-tuning"],
                                    cta: "Contact Sales",
                                    variant: "outline"
                                }
                            ].map((plan, i) => (
                                <Card key={i} className={`relative flex flex-col ${plan.popular ? 'border-primary shadow-2xl shadow-primary/20 scale-105 z-10 bg-card/80' : 'bg-card/40 hover:bg-card/60'} backdrop-blur-sm border-border/50 transition-all`}>
                                    {plan.popular && (
                                        <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1.5 bg-primary text-primary-foreground text-sm font-bold rounded-full shadow-lg">
                                            MOST POPULAR
                                        </div>
                                    )}
                                    <CardHeader>
                                        <CardTitle className="text-2xl">{plan.title}</CardTitle>
                                        <div className="mt-2 flex items-baseline gap-1">
                                            <span className="text-4xl font-bold">{plan.price}</span>
                                            {plan.period && <span className="text-muted-foreground">{plan.period}</span>}
                                        </div>
                                        <CardDescription>{plan.description}</CardDescription>
                                    </CardHeader>
                                    <CardContent className="flex-1">
                                        <ul className="space-y-4 text-sm text-muted-foreground">
                                            {plan.features.map((feature, j) => (
                                                <li key={j} className="flex items-center gap-3">
                                                    <Check className="w-5 h-5 text-primary" />
                                                    {feature}
                                                </li>
                                            ))}
                                        </ul>
                                    </CardContent>
                                    <CardFooter>
                                        <Link href="/" className="w-full">
                                            <Button variant={plan.variant as "default" | "outline"} className="w-full h-12 text-lg">
                                                {plan.cta}
                                            </Button>
                                        </Link>
                                    </CardFooter>
                                </Card>
                            ))}
                        </div>
                    </div>
                </section>

                {/* FAQ Section */}
                <section id="faq" className="py-24">
                    <div className="container mx-auto px-4 md:px-6 max-w-3xl mx-auto space-y-12">
                        <div className="text-center space-y-4">
                            <h2 className="text-4xl font-bold tracking-tight">Frequently Asked Questions</h2>
                            <p className="text-muted-foreground text-xl">
                                Everything you need to know about Verbix AI.
                            </p>
                        </div>

                        <Accordion type="single" collapsible className="w-full">
                            {[
                                { section: "General", q: "What is Verbix AI?", a: "Verbix AI is an all-in-one AI content generation platform that helps you create text, images, and videos in seconds." },
                                { section: "Billing", q: "Can I cancel my subscription anytime?", a: "Yes, you can cancel your subscription at any time. Your access will continue until the end of your billing cycle." },
                                { section: "Technical", q: "Do I need coding skills to use Verbix AI?", a: "Not at all! Verbix AI is designed to be user-friendly and intuitive. If you can type, you can use Verbix AI." },
                                { section: "Privacy", q: "Is my data secure?", a: "Absolutely. We use enterprise-grade encryption and strictly adhere to privacy standards to ensure your data remains safe." }
                            ].map((faq, i) => (
                                <AccordionItem key={i} value={`item-${i}`}>
                                    <AccordionTrigger className="text-lg">{faq.q}</AccordionTrigger>
                                    <AccordionContent className="text-muted-foreground text-base">
                                        {faq.a}
                                    </AccordionContent>
                                </AccordionItem>
                            ))}
                        </Accordion>
                    </div>
                </section>


                {/* CTA Section */}
                <section className="py-32 bg-primary/5 border-y border-primary/10 relative overflow-hidden">
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-primary/10 rounded-full blur-[120px] pointer-events-none" />
                    <div className="container mx-auto px-4 md:px-6 text-center space-y-8 relative z-10">
                        <h2 className="text-4xl md:text-5xl font-bold tracking-tight">Ready to Transform Your Workflow?</h2>
                        <p className="text-muted-foreground text-xl max-w-2xl mx-auto">
                            Join thousands of creators using Verbix AI to build the future of content.
                        </p>
                        <Link href="/">
                            <Button size="lg" className="h-16 px-12 text-xl shadow-2xl shadow-primary/30 hover:shadow-primary/50 transition-all rounded-full">
                                Get Started Now
                            </Button>
                        </Link>
                    </div>
                </section>
            </main>

            <footer className="py-12 border-t border-border/50 bg-background/50 backdrop-blur-sm">
                <div className="container mx-auto px-4 md:px-6 flex flex-col md:flex-row items-center justify-between gap-8 text-muted-foreground">
                    <div className="flex flex-col items-center md:items-start gap-2">
                        <span className="font-bold text-xl text-foreground">Verbix AI</span>
                        <p className="text-sm">© {new Date().getFullYear()} Verbix AI Inc.</p>
                    </div>
                    <div className="flex gap-8 text-sm">
                        <Link href="#" className="hover:text-foreground transition-colors">Privacy Policy</Link>
                        <Link href="#" className="hover:text-foreground transition-colors">Terms of Service</Link>
                        <Link href="#" className="hover:text-foreground transition-colors">Twitter</Link>
                        <Link href="#" className="hover:text-foreground transition-colors">GitHub</Link>
                    </div>
                </div>
            </footer>
        </div>
    );
}
