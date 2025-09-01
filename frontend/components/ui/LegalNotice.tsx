import { Info } from 'lucide-react'
import { LEGAL_CONFIG } from '@/config/legal'
import { cn } from '@/lib/utils'

interface LegalNoticeProps {
  className?: string
}

export function LegalNotice({ className }: LegalNoticeProps) {
  return (
    <div className={cn(
      "flex items-start gap-2 text-xs",
      className
    )}>
      <Info className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 opacity-50" />
      <div className="opacity-60">
        <p>{LEGAL_CONFIG.disclaimer}</p>
        <p className="mt-1 opacity-80">{LEGAL_CONFIG.compliance_notice}</p>
      </div>
    </div>
  )
}