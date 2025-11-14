# Visualization Generation - Ideas & Considerations

**Purpose**: Notes for scoping future visualization generation work (Phase 5)
**Status**: Planning / Ideas Collection
**Created**: 2025-11-14

---

## Core Concept

Enable AI chat agent to generate charts/graphs on-demand in response to natural language queries about fitness data.

**Example User Flow**:
- User: "Show me my heart rate trend for the last 30 days"
- AI: Responds with text insight + inline chart image
- Chart: Line graph showing daily heart rate data

---

## Technical Approach (Two-Stage Process)

### Stage 1: Visualization Specification (Chat Agent)

Chat agent interprets request and creates a structured spec:

```python
class VisualizationSpec(BaseModel):
    chart_type: str  # "line", "bar", "scatter", "heatmap"
    title: str
    metric: str  # "heart_rate", "steps", "distance", etc.
    data_query: dict  # Parameters to fetch from Garmin
    date_range: tuple[str, str]
    aggregation: Optional[str]  # "daily", "weekly", "monthly"
```

**Pydantic-AI Tool**: `visualization_request_tool` - allows agent to request charts

### Stage 2: Chart Generation (Visualization Service)

Backend service generates PNG image:

```python
# app/services/visualization_service.py
async def generate_chart(spec: VisualizationSpec) -> str:
    # 1. Fetch Garmin data based on spec.data_query
    # 2. Generate matplotlib chart
    # 3. Save as PNG
    # 4. Return URL or base64 embed
```

**Dependencies**: `matplotlib`, `Pillow` (PIL)

---

## Design Decisions to Make

### 1. Chart Types to Support

**Options**:
- **Minimal (Phase 5a)**: Line chart only (simplest, proves concept)
- **Standard (Phase 5b)**: Line + Bar + Scatter (covers 80% of use cases)
- **Comprehensive (Phase 5c)**: Add Heatmap, Box plot, Multi-axis (complex but powerful)

**Recommendation**: Start with 2-3 types, expand based on user demand

**Chart Type Use Cases**:
- **Line chart**: Trends over time (heart rate, weight, sleep hours)
- **Bar chart**: Comparisons (weekly distance, activity counts by type)
- **Scatter plot**: Correlations (sleep vs. heart rate, distance vs. pace)
- **Heatmap**: Activity intensity by day/hour
- **Box plot**: Distribution analysis (pace variability, HR zones)

### 2. Image Storage Strategy

**Options**:

**A. Cloud Storage Bucket**:
- ✅ Scalable, CDN-ready
- ✅ Direct URL serving
- ❌ Additional GCP service, cost
- ❌ Requires signed URLs or public bucket

**B. Firestore Embedded (base64)**:
- ✅ No additional service
- ✅ Automatic cleanup with TTL
- ❌ Document size limits (1MB max)
- ❌ Slower to load large images

**C. Temporary Files (Cloud Run filesystem)**:
- ✅ Zero additional cost
- ✅ Automatic cleanup on instance restart
- ❌ Lost on scale-down/restart
- ❌ Not suitable for persistent storage

**D. Hybrid (Generate + Cache)**:
- Generate on-demand, cache in memory for session
- Store spec in Firestore, regenerate on request
- ✅ No persistent storage needed
- ✅ Always fresh data
- ❌ Slower initial load

**Recommendation**: Start with **Option D** (regenerate on-demand) - simplest, no storage costs

### 3. UI Integration (HTMX)

**Where to Display Charts**:

**A. Inline in Chat Messages**:
```html
<div class="message ai">
    <p>Here's your heart rate trend:</p>
    <img src="/viz/abc123.png" alt="Heart Rate Trend" class="rounded-lg shadow-md">
</div>
```
- ✅ Natural conversation flow
- ❌ Can clutter chat history

**B. Modal/Overlay**:
- User clicks "View Chart" button
- Opens full-screen overlay
- ✅ Cleaner chat UI
- ❌ Extra interaction required

**C. Gallery Section**:
- Separate "Visualizations" tab
- All generated charts in one place
- ✅ Easy to compare multiple charts
- ❌ Disconnected from conversation context

**Recommendation**: Start with **A (Inline)**, add **C (Gallery)** in Phase 6

### 4. Chart Styling & Branding

**Options**:
- **Matplotlib defaults**: Fast but generic
- **Seaborn themes**: Better aesthetics, minimal effort
- **Custom styling**: Match TailwindCSS theme (blues, grays)
- **Dark mode support**: Detect user preference, generate matching chart

**Recommendation**: Custom styling to match app theme, defer dark mode to Phase 6

**Styling Checklist**:
- [ ] Font: Match web app (system fonts or Tailwind defaults)
- [ ] Colors: Use brand palette (blues for primary data)
- [ ] Grid: Light gray, subtle
- [ ] Labels: Clear, readable at mobile sizes
- [ ] Legend: Only if multiple series
- [ ] Title: Bold, descriptive

### 5. Performance Considerations

**Spike Validation**: Chart generation in <3 seconds ✅

**Optimization Strategies**:
- **Data caching**: Use existing Garmin cache (24hr TTL)
- **Pre-aggregation**: Store daily summaries (avoid recomputing)
- **Lazy loading**: Generate chart only when user scrolls to it (HTMX hx-trigger="revealed")
- **Background jobs**: Generate during AI response (async)
- **Size limits**: Max 800x600px (mobile-friendly, fast rendering)

**Recommendation**: Start simple, optimize if >3s observed in production

### 6. Data Privacy & Security

**Considerations**:
- Charts may contain sensitive health data (HR, weight, sleep)
- Generated images should not be publicly accessible
- URLs should be time-limited or user-scoped

**Security Options**:
- **Signed URLs**: Short expiry (1 hour), prevents unauthorized access
- **Session-scoped**: Only accessible to logged-in user who requested
- **No persistence**: Regenerate on every view (privacy-first)

**Recommendation**: Session-scoped URLs + regeneration on-demand

### 7. Error Handling

**Failure Scenarios**:
- Insufficient data (user asks for 30 days, only has 5 days)
- Invalid metric (typo or unsupported data type)
- Chart generation timeout
- Matplotlib rendering error

**UX Responses**:
- Graceful degradation: Return text summary if chart fails
- Clear error messages: "Not enough data to generate chart (need 7+ days)"
- Retry option: "Try again" button or regenerate link

**Recommendation**: Always return text response even if chart fails

### 8. Accessibility

**Considerations**:
- Screen readers can't interpret chart images
- Color blindness (avoid red/green for comparisons)
- Alt text must describe data accurately

**Implementation**:
- Generate descriptive alt text: "Line chart showing heart rate from Jan 1-30, ranging from 60-120 bpm, with average of 75 bpm"
- Provide data table as fallback (collapsible)
- Use colorblind-safe palettes (Viridis, Tableau)

**Recommendation**: Generate alt text from spec, defer data table to Phase 6

---

## Open Questions

1. **Multi-metric charts**: Should we support overlaying multiple metrics (e.g., HR + steps on same chart)?
2. **Interactive charts**: Static PNG vs. JavaScript library (Plotly, Chart.js) for zoom/pan?
3. **Export feature**: Allow users to download charts as PNG/SVG/PDF?
4. **Comparison mode**: Side-by-side charts (this week vs. last week)?
5. **Annotations**: Allow AI to highlight notable points (PRs, anomalies)?
6. **Chart suggestions**: Should AI proactively suggest charts, or only respond to requests?

---

## Dependencies

**New Python Packages**:
```toml
[project]
dependencies = [
    "matplotlib>=3.8.0",
    "Pillow>=10.0.0",
    # Optional: seaborn for better defaults
]
```

**Frontend Updates**:
- HTMX: Handle image loading in chat messages
- TailwindCSS: Styles for image containers, loading states
- Alpine.js: Image viewer modal (if using overlay approach)

**Infrastructure**:
- Cloud Storage bucket (if persistent storage chosen)
- Signed URL generation (if using Cloud Storage)

---

## Testing Strategy

**Unit Tests**:
- Chart generation service (mock data input → verify PNG output)
- Visualization spec parsing (natural language → VisualizationSpec)
- Data aggregation functions (raw Garmin data → chart data)

**Integration Tests**:
- Full flow: Request → Spec → Chart → URL
- Error handling (missing data, invalid specs)

**E2E Tests**:
- User asks for chart in chat
- Verify image appears in message
- Verify image URL is accessible (signed correctly)

**Manual Testing**:
- Visual inspection of charts (accurate data, good aesthetics)
- Mobile responsiveness (charts readable on small screens)
- Accessibility (screen reader announces alt text)

**Coverage Target**: 80%+ (consistent with project standards)

---

## Spike Learnings (Already Validated)

From `docs/project-setup/SPIKE_plan.md`:

✅ **Proven in Spike**:
- matplotlib chart generation works
- Performance: <3 seconds for line chart
- File: `spike/viz_generator.py` (reference implementation)

**Spike Code Snippet** (to adapt):
```python
def generate_line_chart(data: list, title: str) -> BytesIO:
    plt.figure(figsize=(10, 6))
    plt.plot(data)
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Value")

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    return buffer
```

---

## Migration from smolagents (Garmin Agents)

**Original `plot_trend` tool** (to refactor):
- Combined data fetching + chart generation (tight coupling)
- Used matplotlib directly in tool
- No spec/service separation

**New Pydantic-AI Approach**:
- Tool returns `VisualizationSpec` only
- Service handles chart generation separately
- Better testability, cleaner separation of concerns

---

## Success Criteria (When Scoping Phase 5)

**Technical**:
- [ ] User can request chart via natural language
- [ ] Chart generates in <5 seconds
- [ ] Chart displays inline in chat message
- [ ] At least 2-3 chart types supported
- [ ] 80%+ test coverage

**User Experience**:
- [ ] Charts are accurate (data matches reality)
- [ ] Charts are readable (clear labels, good contrast)
- [ ] Charts are accessible (alt text, colorblind-safe)
- [ ] Errors are graceful (fallback to text)

**Documentation**:
- [ ] How to add new chart types (developer guide)
- [ ] How to customize chart styling
- [ ] Troubleshooting guide for chart failures

---

## Future Enhancements (Post-Phase 5)

- **Animated charts**: Show trends over time (GIF or video)
- **Interactive charts**: Plotly/Chart.js for zoom, hover tooltips
- **Chart templates**: Pre-built charts (weekly summary, monthly review)
- **Chart sharing**: Generate public URL for social sharing
- **Multi-user charts**: Compare with anonymized community averages
- **AI annotations**: Highlight interesting patterns automatically

---

**Next Steps When Ready**:
1. Review this document during Phase 5 planning
2. Make decisions on open questions
3. Create detailed `PHASE_5_plan.md` with step-by-step tasks
4. Follow TDD workflow (tests first, then implement)
5. Reference spike code (`spike/viz_generator.py`) for patterns

---

*Last Updated: 2025-11-14*
