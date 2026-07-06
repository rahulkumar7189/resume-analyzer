import Link from 'next/link'
import { ArrowRight, Brain, Zap, Shield, CheckCircle2, ChevronRight, BarChart3, FileText, Database } from 'lucide-react'

export default function Home() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-gray-200 flex flex-col relative overflow-x-hidden font-sans selection:bg-primary/30">
      
      {/* Abstract Animated Background Gradients */}
      <div className="absolute top-[-10%] left-[-10%] w-[800px] h-[800px] bg-primary/20 rounded-full blur-[120px] pointer-events-none animate-pulse-slow" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[800px] h-[800px] bg-secondary/20 rounded-full blur-[120px] pointer-events-none animate-pulse-slow" style={{ animationDelay: '1.5s' }} />
      <div className="absolute inset-0 bg-grid-pattern pointer-events-none opacity-50 mix-blend-overlay" />
      
      {/* Navbar */}
      <header className="flex justify-between items-center px-8 py-6 z-20 max-w-7xl mx-auto w-full">
        <div className="flex items-center space-x-3 group cursor-pointer">
          <div className="w-10 h-10 bg-gradient-to-tr from-primary to-secondary rounded-xl flex items-center justify-center shadow-lg shadow-primary/20 group-hover:shadow-primary/40 transition-all">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <span className="font-extrabold text-2xl tracking-tighter text-white">NeuroATS</span>
        </div>
        <div className="flex items-center space-x-6">
          <div className="hidden md:flex space-x-8 text-sm font-medium text-gray-400">
            <a href="#features" className="hover:text-white transition-colors">Platform</a>
            <a href="#how-it-works" className="hover:text-white transition-colors">How it Works</a>
            <a href="#" className="hover:text-white transition-colors">Enterprise</a>
          </div>
          <Link href="/login" className="bg-white/5 hover:bg-white/10 border border-white/10 px-6 py-2.5 rounded-full font-bold text-white transition-all hover:scale-105 active:scale-95 shadow-sm">
            Sign In
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center text-center px-6 z-20 max-w-5xl mx-auto pt-20 pb-32">
        <div className="inline-flex items-center px-4 py-2 rounded-full bg-primary/10 text-primary border border-primary/20 mb-8 font-bold text-sm shadow-[0_0_20px_rgba(59,130,246,0.15)] animate-fade-in">
          <Zap className="w-4 h-4 mr-2" /> Powered by Custom DeBERTa-v3 NLP
        </div>
        
        <h1 className="text-6xl md:text-8xl font-black mb-8 tracking-tighter leading-[1.1] text-white animate-slide-in-bottom">
          Hiring Intelligence, <br/>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 drop-shadow-sm">
            Automated.
          </span>
        </h1>
        
        <p className="text-xl md:text-2xl text-gray-400 mb-12 max-w-3xl leading-relaxed animate-slide-in-bottom" style={{ animationDelay: '0.1s' }}>
          Stop skimming. Start analyzing. NeuroATS uses deep learning NER to extract, normalize, and score candidate skills against your job descriptions in milliseconds.
        </p>
        
        <div className="flex flex-col sm:flex-row items-center gap-4 animate-slide-in-bottom" style={{ animationDelay: '0.2s' }}>
          <Link 
            href="/login" 
            className="group flex items-center bg-white text-black px-8 py-4 rounded-full font-bold text-lg transition-all hover:scale-105 hover:bg-gray-100 shadow-[0_0_40px_rgba(255,255,255,0.2)]"
          >
            Start Free Trial
            <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1.5 transition-transform" />
          </Link>
          <a 
            href="#features" 
            className="flex items-center bg-white/5 hover:bg-white/10 text-white border border-white/10 px-8 py-4 rounded-full font-bold text-lg transition-all backdrop-blur-sm"
          >
            View Features
          </a>
        </div>

        {/* Dashboard Preview mockup */}
        <div className="mt-24 w-full max-w-5xl relative animate-slide-in-bottom" style={{ animationDelay: '0.4s' }}>
          <div className="absolute inset-0 bg-gradient-to-t from-[#0a0a0f] via-transparent to-transparent z-10"></div>
          <div className="relative rounded-t-[2.5rem] border border-white/10 bg-[#0d0d14]/80 backdrop-blur-xl p-4 shadow-2xl overflow-hidden">
            <div className="flex items-center gap-2 mb-6 px-4 pt-2">
              <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
              <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
              <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
            </div>
            <div className="grid grid-cols-3 gap-6 opacity-80">
              <div className="col-span-1 border-r border-white/10 pr-6 space-y-4">
                <div className="h-8 bg-white/5 rounded-lg w-3/4"></div>
                <div className="h-12 bg-primary/20 border border-primary/30 rounded-xl"></div>
                <div className="h-12 bg-white/5 rounded-xl"></div>
                <div className="h-12 bg-white/5 rounded-xl"></div>
              </div>
              <div className="col-span-2 space-y-6">
                 <div className="flex justify-between items-end">
                   <div className="h-10 bg-white/10 rounded-lg w-1/3"></div>
                   <div className="h-16 w-24 bg-secondary/20 border border-secondary/30 rounded-2xl"></div>
                 </div>
                 <div className="h-32 bg-white/5 rounded-2xl border border-white/10"></div>
                 <div className="h-64 bg-white/5 rounded-2xl border border-white/10"></div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Features Grid */}
      <section id="features" className="py-32 px-6 bg-black/40 border-t border-white/5 relative z-20">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-5xl font-black text-white mb-6">Built for the modern recruiter.</h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">Traditional ATS systems look for exact keyword matches. We use context-aware AI to understand semantic meaning and experience depth.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="bg-white/[0.02] border border-white/10 p-10 rounded-3xl backdrop-blur-sm hover:bg-white/[0.04] transition-colors group">
              <div className="w-14 h-14 bg-primary/10 rounded-2xl flex items-center justify-center mb-6 border border-primary/20 group-hover:scale-110 transition-transform">
                <Brain className="w-7 h-7 text-primary" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">Hybrid NER Pipeline</h3>
              <p className="text-gray-400 leading-relaxed">Combines EntityRuler exact matching with custom-trained deep learning to detect skills even when phrased uniquely.</p>
            </div>
            
            <div className="bg-white/[0.02] border border-white/10 p-10 rounded-3xl backdrop-blur-sm hover:bg-white/[0.04] transition-colors group">
              <div className="w-14 h-14 bg-secondary/10 rounded-2xl flex items-center justify-center mb-6 border border-secondary/20 group-hover:scale-110 transition-transform">
                <BarChart3 className="w-7 h-7 text-secondary" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">Section-Aware Scoring</h3>
              <p className="text-gray-400 leading-relaxed">A skill found under "Professional Experience" weighs significantly more than a skill dumped in a "Skills" list.</p>
            </div>

            <div className="bg-white/[0.02] border border-white/10 p-10 rounded-3xl backdrop-blur-sm hover:bg-white/[0.04] transition-colors group">
              <div className="w-14 h-14 bg-emerald-500/10 rounded-2xl flex items-center justify-center mb-6 border border-emerald-500/20 group-hover:scale-110 transition-transform">
                <Database className="w-7 h-7 text-emerald-400" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">Alias Normalization</h3>
              <p className="text-gray-400 leading-relaxed">Automatically normalizes "React.js", "ReactJS", and "React" into a single canonical skill using RapidFuzz logic.</p>
            </div>

            <div className="bg-white/[0.02] border border-white/10 p-10 rounded-3xl backdrop-blur-sm hover:bg-white/[0.04] transition-colors group">
              <div className="w-14 h-14 bg-purple-500/10 rounded-2xl flex items-center justify-center mb-6 border border-purple-500/20 group-hover:scale-110 transition-transform">
                <FileText className="w-7 h-7 text-purple-400" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">Formatting Analysis</h3>
              <p className="text-gray-400 leading-relaxed">Programmatically analyzes bullet points for strong action verbs and quantified metrics, flagging weak phrases.</p>
            </div>

            <div className="bg-white/[0.02] border border-white/10 p-10 rounded-3xl backdrop-blur-sm hover:bg-white/[0.04] transition-colors group lg:col-span-2 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 rounded-full blur-[80px]"></div>
              <div className="relative z-10 flex flex-col md:flex-row gap-8 items-center">
                <div className="flex-1">
                  <div className="w-14 h-14 bg-blue-500/10 rounded-2xl flex items-center justify-center mb-6 border border-blue-500/20 group-hover:scale-110 transition-transform">
                    <Shield className="w-7 h-7 text-blue-400" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-4">Bias-Free & Candidate-Friendly</h3>
                  <p className="text-gray-400 leading-relaxed mb-6">Our system focuses strictly on quantifiable experience and domain skills, ignoring demographics. Candidates get a dedicated portal to view their missing skills and improve their resume formatting.</p>
                  <Link href="/login" className="inline-flex items-center text-primary font-bold hover:text-blue-400 transition-colors">
                    View Candidate Portal <ChevronRight className="w-4 h-4 ml-1" />
                  </Link>
                </div>
                <div className="w-full md:w-64 bg-black/60 border border-white/10 rounded-2xl p-6 shadow-2xl">
                  <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-4">
                    <span className="text-sm font-bold text-gray-300">ATS Score</span>
                    <span className="text-2xl font-black text-green-400">85%</span>
                  </div>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-400">Action Verbs</span>
                      <span className="text-green-400 font-bold">92%</span>
                    </div>
                    <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                      <div className="h-full bg-green-400 w-[92%]"></div>
                    </div>
                    <div className="flex items-center justify-between text-xs mt-4">
                      <span className="text-gray-400">Quantified</span>
                      <span className="text-yellow-400 font-bold">45%</span>
                    </div>
                    <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                      <div className="h-full bg-yellow-400 w-[45%]"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-32 px-6 relative z-20">
        <div className="max-w-4xl mx-auto bg-gradient-to-br from-primary/20 via-secondary/10 to-transparent border border-white/10 rounded-[3rem] p-16 text-center backdrop-blur-xl relative overflow-hidden">
          <div className="absolute inset-0 bg-[url('/noise.png')] opacity-10 mix-blend-overlay"></div>
          <h2 className="text-4xl md:text-5xl font-black text-white mb-6 relative z-10">Ready to transform your hiring?</h2>
          <p className="text-xl text-gray-300 mb-10 max-w-2xl mx-auto relative z-10">Join forward-thinking teams using AI to find the best talent faster, fairer, and with complete transparency.</p>
          <Link href="/login" className="relative z-10 inline-flex items-center bg-white text-black px-10 py-5 rounded-full font-bold text-xl transition-all hover:scale-105 hover:bg-gray-100 shadow-[0_0_40px_rgba(255,255,255,0.3)]">
            Create an Account
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 bg-black py-12 px-8 z-20 text-center md:text-left">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center space-x-2 opacity-50 hover:opacity-100 transition-opacity">
            <Brain className="w-5 h-5" />
            <span className="font-bold text-lg tracking-tighter">NeuroATS</span>
          </div>
          <div className="text-sm text-gray-500">
            © 2026 NeuroATS Technologies. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}
