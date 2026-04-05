document$.subscribe(() => {
  if (!window.mermaid) {
    return;
  }

  window.mermaid.initialize({
    startOnLoad: false,
  });

  for (const element of document.querySelectorAll(".mermaid")) {
    window.mermaid.run({
      nodes: [element],
    });
  }
});
