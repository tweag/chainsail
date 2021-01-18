import SyntaxHighlighter from 'react-syntax-highlighter';
import { github as codeStyle } from 'react-syntax-highlighter/dist/cjs/styles/hljs';
const Code = ({ children, language, inline }) => {
  return (
    <SyntaxHighlighter
      language={language ? language : 'javascript'}
      style={codeStyle}
      useInlineStyles={inline}
    >
      {children}
    </SyntaxHighlighter>
  );
};

export default Code;
