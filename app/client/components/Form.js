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
      className="h-full p-5 text-white rounded-l-lg whitespace-nowrap min-w-min bg-purple-700"
      onClick={() => setActiveField(inputName)}
    >
      <FlexCenter className="w-full h-full">
        {label}
        {optional ? '' : ' *'}
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
      defaultValue={value ? undefined : defaultValue}
      disabled={disabled}
      value={value}
      onChange={onChange}
    />
  </FlexRow>
);

const FileFormField = ({
  disabled,
  label,
  labelIconClassName,
  inputName,
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
      className="h-full p-5 text-white rounded-l-lg whitespace-nowrap min-w-min bg-purple-700"
      onClick={() => setActiveField(inputName)}
    >
      <FlexCenter className="w-full h-full">
        {label}
        {optional ? '' : ' *'}
        {labelIconClassName && <div className={`ml-2 ${labelIconClassName}`}></div>}
      </FlexCenter>
    </label>

    <input
      type="file"
      name={inputName}
      accept=".zip"
      class="form-control block px-3 py-1.5 text-base font-normal text-white bg-clip-padding rounded transition ease-in-out m-0 focus:border-blue-600 focus:outline-none"
      onFocus={() => setActiveField(inputName)}
      onBlur={() => setActiveField('')}
      disabled={disabled}
      onChange={onChange}
    />
  </FlexRow>
);

const options = [
  { label: 'Global tempering', value: 'boltzmann' },
  { label: 'Likelihood tempering', value: 'likelihood_tempered' },
];

const Dropdown = ({
  disabled,
  label,
  labelIconClassName,
  inputName,
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
      className="h-full p-5 text-white rounded-l-lg whitespace-nowrap min-w-min bg-purple-700"
      onClick={() => setActiveField(inputName)}
    >
      <FlexCenter className="w-full h-full">
        {label}
        {optional ? '' : ' *'}
        {labelIconClassName && <div className={`ml-2 ${labelIconClassName}`}></div>}
      </FlexCenter>
    </label>

    <select
      value={value}
      onChange={onChange}
      className="flex-grow h-full px-2 text-black rounded-r-lg"
      disabled={disabled}
    >
      <option value="boltzmann" selected>
        Global tempering
      </option>
      <option value="likelihood_tempered">Likelihood tempering</option>
    </select>
  </FlexRow>
);

export { FormField, FileFormField, Dropdown };
