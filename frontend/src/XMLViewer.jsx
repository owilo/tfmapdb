import React, { useState } from "react";
import { parse } from "txml";
import { ChevronRight } from "lucide-react";
import './style/main.css';

function CollapseButton({ isOpen, onToggle }) {
  return (
    <button
      onClick={onToggle}
      aria-label={isOpen ? "Collapse node" : "Expand node"}
      className="
        flex items-center justify-center w-6 h-6 p-1
        mr-1
        rounded
        filter hover:brightness-110 transition-all duration-200
        focus:outline-none focus:ring-0
      "
    >
      <ChevronRight
        className={`
          w-4 h-4
          transition-transform duration-200
          ${isOpen ? "rotate-90" : ""}
        `}
      />
    </button>
  );
}

export default function XMLViewer({ xml, theme = {}, indentSize = 4 }) {
  const tree = parse(xml);
  const [expandedMap, setExpandedMap] = useState({});
  const toggle = (path) => {
    setExpandedMap((m) => {
      const currentlyOpen = m[path] !== undefined ? m[path] : true;
      return { ...m, [path]: !currentlyOpen };
    });
  };

  const fullRows = [];
  const buildRows = (node, path, depth) => {
    // Opening row
    fullRows.push({ type: "open", node, depth, path });

    // Child elements and text rows
    (node.children || []).forEach((child, idx) => {
      if (typeof child === "object") {
        buildRows(child, `${path}-${idx}`, depth + 1);
      } else if (typeof child === "string" && child.trim()) {
        fullRows.push({ type: "text", text: child.trim(), depth: depth + 1, path: `${path}-text-${idx}` });
      }
    });

    // Only append a closing row if there are any children
    if ((node.children || []).length > 0) {
      fullRows.push({ type: "close", node, depth, path });
    }
  };
  tree.forEach((node, idx) => buildRows(node, `${idx}`, 0));

  fullRows.forEach((row, idx) => (row.lineNumber = idx + 1));

  const defaultTheme = {
    container: "bg-gray-50 p-2 font-mono text-sm overflow-auto",
    lineNumber: "min-w-8 max-w-8 inline-block text-gray-400 select-none",
    tagBracket: "text-blue-500",
    tagName: "text-purple-600",
    attrName: "text-yellow-500",
    attrValue: "text-green-500",
    textNode: "text-gray-700",
  };
  const cls = { ...defaultTheme, ...theme };

  // Render visible rows
  const lines = [];
  for (let i = 0; i < fullRows.length; i++) {
    const { type, node, text, depth, path, lineNumber } = fullRows[i];
    const paddingStyle = { paddingLeft: `${depth * indentSize}ch` };
    const children = node.children || [];
    const elementCount = children.filter((c) => typeof c === "object").length;
    const isOpen = expandedMap[path] !== undefined ? expandedMap[path] : true;

    // Collapsed summary
    if (type === "open" && elementCount > 0 && !isOpen) {
      lines.push(
        <div key={`${path}-collapsed`} className="flex whitespace-nowrap">
          <span className={cls.lineNumber}>{lineNumber}</span>
          <div className="flex items-center" style={paddingStyle}>
            <CollapseButton isOpen={false} onToggle={() => toggle(path)} />
            <span className={cls.tagBracket}>&lt;</span>
            <span className={cls.tagName}>{node.tagName}</span>
            {Object.entries(node.attributes || {}).map(([n, v], idx) => (
              <React.Fragment key={idx}>
                &nbsp;<span className={cls.attrName}>{n}</span>=<span className={cls.attrValue}>&quot;{v}&quot;</span>
              </React.Fragment>
            ))}
            <span className={cls.tagBracket}>&gt;</span>
            <span className="text-gray-400 select-none">
              &nbsp;{children.length} item(s)&nbsp;
            </span>
            <span className={cls.tagBracket}>&lt;/</span>
            <span className={cls.tagName}>{node.tagName}</span>
            <span className={cls.tagBracket}>&gt;</span>
          </div>
        </div>
      );
      // Skip subtree rows
      const skipCount = fullRows.slice(i + 1).findIndex((r) => !r.path.startsWith(path + "-"));
      i += skipCount === -1 ? fullRows.length : skipCount;
      continue;
    }

    // Opening tag row
    if (type === "open") {
      lines.push(
        <div key={`${path}-open`} className="flex whitespace-nowrap">
          <span className={cls.lineNumber}>{lineNumber}</span>
          <div className="flex items-center" style={paddingStyle}>
            {elementCount > 0 ? (
              <CollapseButton isOpen={isOpen} onToggle={() => toggle(path)} />
            ) : (
              <span className="inline-block w-6 h-6 mr-1" />
            )}
            <span className={cls.tagBracket}>&lt;</span>
            <span className={cls.tagName}>{node.tagName}</span>
            {Object.entries(node.attributes || {}).map(([n, v], idx) => (
              <React.Fragment key={idx}>
                &nbsp;<span className={cls.attrName}>{n}</span>=<span className={cls.attrValue}>&quot;{v}&quot;</span>
              </React.Fragment>
            ))}
            <span className={cls.tagBracket}>{elementCount > 0 ? ">" : "\u00A0/>"}</span>
          </div>
        </div>
      );
    }

    // Text node row
    else if (type === "text") {
      lines.push(
        <div key={path} className="flex whitespace-nowrap">
          <span className={cls.lineNumber}>{lineNumber}</span>
          <div className="flex items-center" style={paddingStyle}>
            <span className="inline-block w-6 h-6 mr-1" />
            <span className={cls.textNode}>{text}</span>
          </div>
        </div>
      );
    }

    // Closing tag row
    else if (type === "close" && elementCount > 0 && isOpen) {
      lines.push(
        <div key={`${path}-close`} className="flex whitespace-nowrap">
          <span className={cls.lineNumber}>{lineNumber}</span>
          <div className="flex items-center" style={paddingStyle}>
            <span className="inline-block w-6 h-6 mr-1" />
            <span className={cls.tagBracket}>&lt;/</span>
            <span className={cls.tagName}>{node.tagName}</span>
            <span className={cls.tagBracket}>&gt;</span>
          </div>
        </div>
      );
    }
  }

  return (
    <div className={`${cls.container} overflow-x-scroll`}>
      {lines}
    </div>
  );
}
