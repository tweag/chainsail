import { FlexRow, FlexCenter } from './Flex';

const FormField = ({
  disabled,
  label,
  labelIconClassName,
  inputName,
  inputType,
  minNumber,
  maxNumber,
  stepNumber,
  defaultValue,
  placeholder,
  setActiveField,
  className,
  width,
  value,
  onChange,
  optional,
}) => (
  <FlexRow className={`h-10 text-xs md:text-base ${width ? width : 'w-full'} ${className}`}>
    <label
      className={`h-full p-5 text-white rounded-l-lg whitespace-nowrap min-w-min 
      ${optional ? 'bg-purple-500' : 'bg-purple-700'}
	    `}
      onClick={() => setActiveField(inputName)}
    >
      <FlexCenter className="w-full h-full">
        {label}
        {labelIconClassName && <div className={`ml-2 ${labelIconClassName}`}></div>}
      </FlexCenter>
    </label>
    <input
      min={inputType === 'number' ? minNumber : ''}
      max={inputType === 'number' ? maxNumber : ''}
      step={inputType === 'number' ? stepNumber : ''}
      type={inputType ? inputType : 'text'}
      name={inputName}
      className="flex-grow h-full px-2 text-black rounded-r-lg"
      onFocus={() => setActiveField(inputName)}
      onBlur={() => setActiveField('')}
      onClick={() => setActiveField(inputName)}
      placeholder={placeholder}
      defaultValue={defaultValue}
      disabled={disabled}
      value={value}
      onChange={onChange}
    />
  </FlexRow>
);

export { FormField };
