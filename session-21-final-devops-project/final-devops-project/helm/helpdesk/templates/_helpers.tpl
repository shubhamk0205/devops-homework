{{/* common labels for every object */}}
{{- define "helpdesk.labels" -}}
app.kubernetes.io/part-of: helpdesk
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}
