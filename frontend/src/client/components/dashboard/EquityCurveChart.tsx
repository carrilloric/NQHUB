/**
 * EquityCurveChart Component
 *
 * D3-based equity curve visualization with drawdown overlay.
 * This is the ONLY component in the entire project using D3.
 *
 * Features:
 * - Equity line (blue #3b82f6)
 * - Drawdown area (red semi-transparent #ef444440)
 * - Smooth transitions (300ms)
 * - Tooltip on hover
 * - Updates in real-time via WebSocket
 */
import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { PortfolioSnapshot } from '@/stores/websocketStore';

interface EquityCurveChartProps {
  data: PortfolioSnapshot[];
  width?: number;
  height?: number;
}

interface DataPoint {
  ts: Date;
  equity: number;
  drawdown: number;
}

export function EquityCurveChart({ data, width = 600, height = 300 }: EquityCurveChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current || data.length === 0) return;

    // Clear previous render
    d3.select(svgRef.current).selectAll('*').remove();

    // Parse data
    const parsedData: DataPoint[] = data.map((d) => ({
      ts: new Date(d.ts),
      equity: d.total_value ?? d.unrealized_pnl ?? 0,
      drawdown: Math.min(0, d.unrealized_pnl ?? 0),
    }));

    // Dimensions
    const margin = { top: 20, right: 30, bottom: 30, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Create SVG
    const svg = d3
      .select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Scales
    const xScale = d3
      .scaleTime()
      .domain(d3.extent(parsedData, (d) => d.ts) as [Date, Date])
      .range([0, innerWidth]);

    const yScale = d3
      .scaleLinear()
      .domain([
        Math.min(0, d3.min(parsedData, (d) => d.drawdown) ?? 0),
        d3.max(parsedData, (d) => d.equity) ?? 0,
      ])
      .nice()
      .range([innerHeight, 0]);

    // Axes
    const xAxis = d3.axisBottom(xScale).ticks(5);
    const yAxis = d3.axisLeft(yScale).ticks(5);

    svg
      .append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(xAxis)
      .selectAll('text')
      .style('font-size', '12px');

    svg.append('g').call(yAxis).selectAll('text').style('font-size', '12px');

    // Grid lines
    svg
      .append('g')
      .attr('class', 'grid')
      .attr('opacity', 0.1)
      .call(d3.axisLeft(yScale).tickSize(-innerWidth).tickFormat(() => ''));

    // Baseline (y=0)
    svg
      .append('line')
      .attr('x1', 0)
      .attr('x2', innerWidth)
      .attr('y1', yScale(0))
      .attr('y2', yScale(0))
      .attr('stroke', '#9ca3af')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '4,4');

    // Drawdown area (red semi-transparent)
    const areaDrawdown = d3
      .area<DataPoint>()
      .x((d) => xScale(d.ts))
      .y0(yScale(0))
      .y1((d) => yScale(d.drawdown));

    svg
      .append('path')
      .datum(parsedData)
      .attr('fill', '#ef444440')
      .attr('d', areaDrawdown)
      .transition()
      .duration(300);

    // Equity line (blue)
    const lineEquity = d3
      .line<DataPoint>()
      .x((d) => xScale(d.ts))
      .y((d) => yScale(d.equity));

    svg
      .append('path')
      .datum(parsedData)
      .attr('fill', 'none')
      .attr('stroke', '#3b82f6')
      .attr('stroke-width', 2)
      .attr('d', lineEquity)
      .transition()
      .duration(300);

    // Tooltip interaction
    const tooltip = d3.select(tooltipRef.current);

    const bisect = d3.bisector<DataPoint, Date>((d) => d.ts).left;

    svg
      .append('rect')
      .attr('width', innerWidth)
      .attr('height', innerHeight)
      .attr('opacity', 0)
      .on('mousemove', function (event) {
        const [xPos] = d3.pointer(event);
        const x0 = xScale.invert(xPos);
        const i = bisect(parsedData, x0, 1);
        const d0 = parsedData[i - 1];
        const d1 = parsedData[i];

        if (!d0 || !d1) return;

        const d = x0.getTime() - d0.ts.getTime() > d1.ts.getTime() - x0.getTime() ? d1 : d0;

        tooltip
          .style('display', 'block')
          .style('left', `${event.pageX + 10}px`)
          .style('top', `${event.pageY - 28}px`)
          .html(
            `<div class="text-xs">
              <div><strong>${d.ts.toLocaleTimeString()}</strong></div>
              <div>Equity: <span class="text-blue-600">$${d.equity.toFixed(2)}</span></div>
              <div>Drawdown: <span class="text-red-600">$${d.drawdown.toFixed(2)}</span></div>
            </div>`
          );
      })
      .on('mouseout', function () {
        tooltip.style('display', 'none');
      });
  }, [data, width, height]);

  return (
    <div className="relative" data-testid="equity-curve-chart">
      <svg ref={svgRef} />
      <div
        ref={tooltipRef}
        style={{ display: 'none' }}
        className="pointer-events-none absolute z-10 rounded bg-white px-2 py-1 shadow-lg"
      />
    </div>
  );
}
