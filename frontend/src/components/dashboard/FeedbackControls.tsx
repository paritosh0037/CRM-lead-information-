"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { acceptRecommendation, overrideRecommendation } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Label } from "@/components/ui/label";

interface Props {
  leadId: string;
  originalAction: string;
}

const SUPPORTED_ACTIONS = ["CALL", "EMAIL", "DEMO", "NURTURE", "REVIEW"];

export default function FeedbackControls({ leadId, originalAction }: Props) {
  const queryClient = useQueryClient();
  const [isOverriding, setIsOverriding] = useState(false);
  const [overrideAction, setOverrideAction] = useState<string>("");
  const [reason, setReason] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const acceptMutation = useMutation({
    mutationFn: () => acceptRecommendation(leadId, originalAction),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lead-feedback", leadId] });
      setIsOverriding(false);
      setReason("");
    },
    onError: (err: Error) => setErrorMsg(err.message),
  });

  const overrideMutation = useMutation({
    mutationFn: () => overrideRecommendation(leadId, originalAction, overrideAction, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lead-feedback", leadId] });
      setIsOverriding(false);
      setReason("");
      setOverrideAction("");
    },
    onError: (err: Error) => setErrorMsg(err.message),
  });

  const handleOverrideSubmit = () => {
    setErrorMsg("");
    if (!overrideAction) {
      setErrorMsg("Please select an override action.");
      return;
    }
    if (!reason.trim()) {
      setErrorMsg("A reason is required when overriding a recommendation.");
      return;
    }
    overrideMutation.mutate();
  };

  return (
    <div className="mt-8 border-t border-line-200 pt-6">
      <h3 className="text-sm font-medium mb-4">Feedback</h3>
      
      {errorMsg && (
        <Alert variant="destructive" className="mb-4 text-xs py-2">
          <AlertDescription>{errorMsg}</AlertDescription>
        </Alert>
      )}

      {!isOverriding ? (
        <div className="flex gap-3">
          <Button 
            className="flex-1 bg-signal-600 hover:bg-signal-600/90 text-white shadow-none rounded-sm"
            onClick={() => acceptMutation.mutate()}
            disabled={acceptMutation.isPending}
          >
            {acceptMutation.isPending ? "Accepting..." : "Accept"}
          </Button>
          <Button 
            variant="outline" 
            className="flex-1 text-flag-600 border-line-200 hover:bg-paper-50 shadow-none rounded-sm"
            onClick={() => setIsOverriding(true)}
          >
            Override
          </Button>
        </div>
      ) : (
        <div className="space-y-4 bg-white p-4 border border-line-200 rounded-sm">
          <div className="space-y-1.5">
            <Label className="text-xs text-ink-900/60">New Action</Label>
            <Select value={overrideAction} onValueChange={(val) => setOverrideAction(val || "")}>
              <SelectTrigger className="shadow-none h-8 text-sm rounded-sm">
                <SelectValue placeholder="Select action..." />
              </SelectTrigger>
              <SelectContent>
                {SUPPORTED_ACTIONS.filter(a => a !== originalAction).map(act => (
                  <SelectItem key={act} value={act}>{act}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <div className="space-y-1.5">
            <Label className="text-xs text-ink-900/60">Why are you choosing a different action?</Label>
            <Textarea 
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="resize-none h-20 shadow-none text-sm rounded-sm"
            />
          </div>

          <div className="flex gap-2 justify-end">
            <Button 
              variant="ghost" 
              size="sm"
              className="text-xs"
              onClick={() => { setIsOverriding(false); setErrorMsg(""); }}
            >
              Cancel
            </Button>
            <Button 
              size="sm"
              className="bg-flag-600 hover:bg-flag-600/90 text-white shadow-none rounded-sm text-xs"
              onClick={handleOverrideSubmit}
              disabled={overrideMutation.isPending}
            >
              {overrideMutation.isPending ? "Submitting..." : "Submit Override"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
