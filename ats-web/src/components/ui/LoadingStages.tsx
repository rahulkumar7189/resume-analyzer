import React, { useEffect, useState } from 'react'
import { Loader2, CheckCircle2, Circle } from 'lucide-react'

const STAGES = [
  "Uploading document...",
  "Parsing PDF and extracting text...",
  "Running Named Entity Recognition...",
  "Evaluating skills against job description...",
  "Querying LLM for holistic feedback...",
  "Finalizing ATS score..."
]

export function LoadingStages() {
  const [currentStage, setCurrentStage] = useState(0)

  useEffect(() => {
    // Simulate progression through stages since the API is synchronous
    // We'll space out the stages over ~3-4 seconds
    const interval = setInterval(() => {
      setCurrentStage((prev) => {
        if (prev < STAGES.length - 1) return prev + 1
        return prev
      })
    }, 1200) // 1.2s per stage

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="w-full max-w-md mx-auto p-6 rounded-2xl bg-black/40 border border-white/10 backdrop-blur-md">
      <h3 className="text-white font-bold mb-6 text-center">Processing Application</h3>
      <div className="space-y-4">
        {STAGES.map((stage, index) => {
          const isCompleted = index < currentStage
          const isCurrent = index === currentStage
          const isPending = index > currentStage

          return (
            <div key={stage} className={`flex items-center gap-3 transition-opacity duration-300 ${isPending ? 'opacity-30' : 'opacity-100'}`}>
              {isCompleted ? (
                <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0" />
              ) : isCurrent ? (
                <Loader2 className="w-5 h-5 text-primary animate-spin shrink-0" />
              ) : (
                <Circle className="w-5 h-5 text-gray-600 shrink-0" />
              )}
              <span className={`text-sm ${isCurrent ? 'text-white font-medium animate-pulse' : isCompleted ? 'text-gray-300' : 'text-gray-500'}`}>
                {stage}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
